import json
import re
from typing import Any, Dict, List, Optional, Tuple

from rag.prompt_template import build_prompt, SYSTEM_PROMPT

# How many retrieved chunks are given to the LLM (retrieval itself still returns more)
TOP_K_FOR_ANSWER = 6

# Set to False only if the verifier rejects too many good answers during testing
STRICT_VERIFY = True

NO_MATCH_MESSAGE = (
    "I couldn't find reliable information in my sources to answer that safely. "
    "I'd rather say so than guess. Please ask a doctor or pharmacist about this."
)

UNVERIFIED_MESSAGE = (
    "I found some related material, but I couldn't confirm that an answer would be fully "
    "supported by my sources, so I'm not going to give one. Please speak to a doctor about this."
)

ERROR_MESSAGE = "Sorry, I'm having trouble processing this right now. Please try again in a moment."

DISCLAIMER = (
    "*This is general information, not a diagnosis. If you are worried about your symptoms, "
    "please see a doctor. If you have severe breathlessness, blue lips, or cannot speak in full "
    "sentences, call emergency services right away (112 in India, 911 in the US).*"
)


MARKER_RE = re.compile(r"[\[\u3010]\s*(\d{1,2})\s*[\]\u3011]")


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _meta(doc: Any, *keys: str, default: str = "") -> str:
    md = getattr(doc, "metadata", None) or {}
    for k in keys:
        v = md.get(k)
        if v:
            return str(v)
    return default


class RAGPipeline:

    def __init__(self, retrieval_pipeline, llm, judge_llm=None):
        self.retrieval_pipeline = retrieval_pipeline
        self.llm = llm
        self.judge_llm = judge_llm or llm  # model used for the faithfulness check

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _result(status: str, answer: str = "", citations: List[dict] = None) -> Dict[str, Any]:
        citations = citations or []
        return {
            "status": status,
            "answer": answer,
            "question": None,
            "citations": citations,
            "sources_count": len(citations),
        }

    def _build_sources(self, docs: List[Any]) -> Tuple[str, List[dict]]:
        """Numbered SOURCES block for the prompt + matching citation records."""
        blocks, items = [], []
        for i, doc in enumerate(docs, start=1):
            text = _clean(getattr(doc, "page_content", ""))
            source = _meta(doc, "source", "Source", default="Unknown source")
            title = _clean(_meta(doc, "title", "Title"))
            url = _meta(doc, "source_url", "url")
            chunk_id = _meta(doc, "chunk_id", "id", default=f"chunk-{i}")
            blocks.append(f"[{i}] ({source}{' - ' + title if title else ''})\n{text[:1500]}")
            snippet = text[len(title):].strip() if title and text.startswith(title) else text
            if len(snippet) > 700:
                snippet = snippet[:700].rsplit(" ", 1)[0] + "..."
            items.append({
                "source": source,
                "chunk_id": chunk_id,
                "title": title,
                "url": url,
                "text": snippet,
            })
        return "\n\n".join(blocks), items

    def _generate(self, sources_text: str, query: str, strict: bool = False) -> str:
        system = SYSTEM_PROMPT
        if strict:
            system += (
                "\nSTRICT MODE: Only write sentences you can copy or very closely paraphrase from a "
                "SOURCE. Remove anything you are not sure is stated there. If little is left, reply NO_ANSWER."
            )
        response = self.llm.invoke([
            {"role": "system", "content": system},
            {"role": "user", "content": build_prompt(sources_text, query)},
        ])
        return (response.content or "").strip()

    # ------------------------------------------------------ faithfulness check
    @staticmethod
    def _norm(text: str) -> str:
        text = MARKER_RE.sub(" ", text or "")
        text = re.sub(r"[*_`>#-]", " ", text.lower())
        return " ".join(re.sub(r"[^a-z0-9 ]", " ", text).split())

    def _find_unsupported(self, sources_text: str, answer: str) -> Optional[List[str]]:
        """Ask the judge model which sentences of the answer the SOURCES do not support.
        Returns a list (empty = everything supported) or None if the check itself failed."""
        prompt = f"""You check an ANSWER against its SOURCES.

SOURCES:
{sources_text}

ANSWER:
{answer}

List every sentence or bullet of the ANSWER that states a medical fact the SOURCES do not support.
A paraphrase or a reasonable summary of what a source says counts as supported.
Ignore citation markers like [1], formatting, and generic advice to see a doctor.
Reply with ONLY a JSON list of strings, copying each unsupported sentence or bullet exactly.
Reply [] if every medical claim is supported."""
        try:
            response = self.judge_llm.invoke([{"role": "user", "content": prompt}])
            raw = (response.content or "").strip()
            raw = re.sub(r"```(?:json)?", "", raw)
            i, j = raw.find("["), raw.rfind("]")
            if i < 0 or j < i:
                print(f"[faithfulness] could not read the judge reply: {raw[:80]!r}")
                return None
            items = json.loads(raw[i:j + 1])
            return [str(x) for x in items if str(x).strip()]
        except Exception as e:
            print(f"[faithfulness] check failed: {e}")
            return None

    def _verify_and_trim(self, sources_text: str, answer: str) -> Tuple[bool, str]:
        """Faithfulness check at claim level.

        Unsupported lines are removed from the answer; the rest is kept if it still says
        something. The answer is refused only when most of it is unsupported or the check fails.
        (The old version tested `"SAFE" in reply`, and "UNSAFE" contains "SAFE", so it never refused.)
        """
        unsupported = self._find_unsupported(sources_text, answer)
        if unsupported is None:
            return False, answer  # fail closed
        if not unsupported:
            print("[faithfulness] all claims supported")
            return True, answer

        bad = [self._norm(u) for u in unsupported if self._norm(u)]
        lines = answer.split("\n")
        kept, removed, cited_total = [], 0, 0
        for line in lines:
            n = self._norm(line)
            has_marker = bool(MARKER_RE.search(line))
            cited_total += 1 if has_marker else 0
            hit = False
            if n and len(n) > 15:
                for b in bad:
                    a, c = set(n.split()), set(b.split())
                    if b in n or n in b or (a and c and len(a & c) / len(a | c) >= 0.6):
                        hit = True
                        break
            if hit:
                removed += 1
                continue
            kept.append(line)

        # drop headings that lost all their content
        cleaned = []
        for k, line in enumerate(kept):
            is_heading = bool(re.match(r"^\*\*[^*]+\*\*:?\s*$", line.strip()))
            nxt = next((l for l in kept[k + 1:] if l.strip()), "")
            if is_heading and (not nxt or re.match(r"^\*\*[^*]+\*\*:?\s*$", nxt.strip())):
                continue
            cleaned.append(line)
        trimmed = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()

        print(f"[faithfulness] {len(unsupported)} unsupported claim(s) reported, {removed} line(s) removed")
        if removed == 0:
            return False, answer  # reported claims could not be located: refuse
        if not MARKER_RE.search(trimmed) or removed > max(1, cited_total // 2):
            return False, answer  # most of the answer was unsupported
        return True, trimmed

    # --------------------------------------------------------------------- main
    def run(self, query: str) -> Dict[str, Any]:
        # 1. Retrieve
        try:
            documents = self.retrieval_pipeline.retrieve(query)
        except Exception as e:
            print(f"[retrieval] error: {e}")
            return self._result("no_match", ERROR_MESSAGE)

        documents = (documents or [])[:TOP_K_FOR_ANSWER]
        if not documents:
            return self._result("no_match", NO_MATCH_MESSAGE)

        sources_text, items = self._build_sources(documents)

        # 2. Generate (retry once in strict mode if verification fails)
        answer = ""
        verified = False
        for strict in (False, True):
            try:
                answer = self._generate(sources_text, query, strict=strict)
            except Exception as e:
                print(f"[generate] error: {e}")
                return self._result("no_match", ERROR_MESSAGE)

            # 3. No-match: the model says the sources can't answer
            if not answer or "NO_ANSWER" in answer.upper():
                return self._result("no_match", NO_MATCH_MESSAGE)

            # 4. Faithfulness verification (unsupported lines are trimmed, not the whole answer)
            if not STRICT_VERIFY:
                verified = True
                break
            ok, answer = self._verify_and_trim(sources_text, answer)
            if ok:
                verified = True
                break

        if not verified:
            return self._result("no_match", UNVERIFIED_MESSAGE)

        # 5. Citations: only the sources the answer actually used.
        # The model sometimes writes 【1】 instead of [1]; both are accepted. The markers are
        # renumbered in order of first use so that [1], [2]... match the returned citations list.
        order = []
        for m in MARKER_RE.finditer(answer):
            n = int(m.group(1))
            if 1 <= n <= len(items) and n not in order:
                order.append(n)
        mapping = {old: new for new, old in enumerate(order, start=1)}

        def renumber(m):
            n = int(m.group(1))
            return f"[{mapping[n]}]" if n in mapping else ""

        if order:
            answer = MARKER_RE.sub(renumber, answer)
            citations = [items[n - 1] for n in order]
        else:
            citations = items[:3]

        return self._result("answer", f"{answer}\n\n{DISCLAIMER}", citations)
