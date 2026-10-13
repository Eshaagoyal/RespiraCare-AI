import json
import re
from typing import List, Optional

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# DB setup and models
from database import get_db, init_db, User, ChatMessage

# RAG system and guardrails
from ai_core import initialize_system
from safety.guardrails import Guardrails

print("Initializing backend AI components...")
rag_system = initialize_system()
guard = Guardrails()
fast_llm = getattr(rag_system, "fast_llm", rag_system.llm)  # small model for triage and chat memory
print("Backend AI ready.")

init_db()

app = FastAPI(title="RespiraCare AI API (asthma)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_CLARIFY = 2  # never ask more than 2 follow-ups in a row

DEFAULT_QUESTION = (
    "Could you tell me a bit more, such as how long this has been going on, "
    "whether you hear wheezing or cough more at night, and what seems to set it off "
    "(exercise, dust, cold air, pollen)?"
)

SCOPE_MESSAGE = (
    "RespiraCare AI currently covers **asthma** only. For other breathing conditions "
    "such as COPD, bronchitis or pneumonia, please speak to a doctor. "
    "I'm happy to answer any question about asthma."
)

EMERGENCY_MESSAGE = (
    "**This could be serious. Please get urgent medical help now.**\n\n"
    "Call your local emergency number (112 in India, 911 in the US) or go to the nearest "
    "emergency department. If someone is nearby, ask them to stay with you. "
    "Please don't wait for an online answer.\n\n"
    "I'm happy to share general information once you are safe."
)

EMERGENCY_PATTERNS = [
    # "can't breathe" in its common spellings and typos (cant breath, cant just breathe, cannot breathe...)
    r"\bcan'?t (just |even |really |properly |hardly |at all )?breathe?\b(?! through (my )?nose)",
    r"\bcannot (just |even |properly )?breathe?\b(?! through (my )?nose)",
    r"\bcan ?not breathe?\b(?! through (my )?nose)",
    r"\b(unable|not able) to breathe?\b", r"\bstruggling to breathe?\b", r"\bgasping for (air|breath)\b",
    r"\bcan'?t catch my breath\b", r"\b(very|really|extremely) hard to breathe?\b", r"\bhardly able to breathe?\b",
    r"blue (lips|fingernails|face)", r"lips? (are|is|turn\w*|look\w*|went) blue", r"turning blue",
    r"can'?t (speak|talk)", r"unable to (speak|talk)",
    r"severe chest pain", r"crushing chest", r"chest pain (is )?(severe|getting worse)",
    r"cough\w* (up )?blood",
    r"passed out", r"fainted", r"unconscious", r"collaps",
    r"inhaler (is )?(not|isn'?t|doesn'?t|won'?t) (work|help)\w*",
    # other ways of saying it
    r"\bsuffocat\w*", r"\bchok(e|ed|ing)\b", r"\bcan'?t get (any |enough )?(air|breath)\b",
    r"\bi('m| am) (dying|going to die)\b", r"\bi (think|feel) i('m| am| will) (dying|die)\b",
    # Hinglish
    r"saans (nahi|nhi|nai) (aa|le|li)", r"dam ghut",
]
_EMERGENCY_RE = re.compile("|".join(EMERGENCY_PATTERNS))


# ------------------------------------------------------------------ schemas
class ChatRequest(BaseModel):
    user_id: int
    query: str


class Citation(BaseModel):
    source: str = ""
    chunk_id: str = ""
    title: str = ""
    url: str = ""
    text: str = ""


class ChatResponse(BaseModel):
    status: str  # answer | clarify | no_match | blocked | emergency
    response: str = ""  # plain text for the current chat page (answer or question, plus sources)
    answer: str = ""
    question: Optional[str] = None
    citations: List[Citation] = []
    sources_count: int = 0


def build_plain_text(result):
    """One plain-text string for the current React chat page: the answer plus a Sources list."""
    if result["status"] == "clarify":
        return result.get("question") or ""
    text = result.get("answer") or ""
    if result["status"] == "answer" and result.get("citations"):
        lines = ["", "", "Sources:"]
        for i, c in enumerate(result["citations"], start=1):
            line = f"[{i}] {c.get('source', '')}: {c.get('title', '')}"
            if c.get("url"):
                line += f" ({c['url']})"
            lines.append(line)
        text += "\n".join(lines)
    return text


def make_result(status, answer="", question=None, citations=None):
    citations = citations or []
    return {
        "status": status,
        "answer": answer,
        "question": question,
        "citations": citations,
        "sources_count": len(citations),
    }


# ------------------------------------------------------------------ helpers
def is_emergency(text: str) -> bool:
    t = (text or "").lower().replace("\u2019", "'")
    return _EMERGENCY_RE.search(t) is not None


def _parse_json(text: str):
    text = re.sub(r"```(?:json)?", "", text or "").strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def reformulate_query(history_text: str, query: str, llm) -> str:
    """Merge chat history into one standalone message (memory)."""
    if not history_text:
        return query
    prompt = f"""You rewrite messages for a respiratory health assistant.

RECENT CHAT:
{history_text}

LATEST PATIENT MESSAGE:
{query}

TASK:
Rewrite the LATEST PATIENT MESSAGE as ONE standalone message that includes the relevant symptoms and details the patient already gave in RECENT CHAT (for example symptoms, duration, smoking).
If the latest message is about a new, unrelated topic, or is already complete, return it unchanged.
Do not answer it. Do not add any detail the patient did not say.

STANDALONE MESSAGE:"""
    try:
        response = llm.invoke([{"role": "user", "content": prompt}])
        text = (response.content or "").strip()
        return text or query
    except Exception as e:
        print(f"[memory] reformulate failed: {e}")
        return query


def triage_query(query: str, llm) -> dict:
    """Decide the scope of the message and whether it has enough detail to answer safely."""
    prompt = f"""You are the triage step of an ASTHMA information assistant.
Decide (1) whether the message is in scope and (2) whether it has enough detail to search medical sources and answer safely.

MESSAGE (already merged with chat history): "{query}"

Reply with ONLY this JSON:
{{"scope": "asthma_or_unclear" or "other_condition" or "off_topic", "enough": true or false, "question": "one short follow-up question, or empty"}}

SCOPE RULES
- other_condition: the person clearly asks about another illness (COPD, bronchitis, pneumonia, COVID, heart disease, and so on) and not about asthma.
- off_topic: not about health at all (greeting, sports, general chat).
- asthma_or_unclear: about asthma, OR about breathing symptoms (cough, wheeze, breathlessness, chest tightness) without naming another illness.

ENOUGH RULES
- enough = true if: it is a general asthma question (for example "What triggers asthma?"), or scope is off_topic, or the person gave a symptom PLUS at least one useful detail (duration, trigger, time of day, exercise, allergies, smoking, severity, or an existing asthma diagnosis).
- enough = false only if it is vague, such as one symptom or a few symptoms with no other detail ("I have a cough", "difficulty breathing").
- If enough is false, ask ONE short, friendly question that asks for the most useful missing details (duration, wheezing or night cough, triggers).
- Never diagnose. Never say the person has asthma. Never assume any medication or inhaler."""
    try:
        response = llm.invoke([{"role": "user", "content": prompt}])
        data = _parse_json(response.content)
    except Exception as e:
        print(f"[triage] failed: {e}")
        data = None

    if not data:
        return {"scope": "asthma_or_unclear", "enough": True, "question": ""}

    scope = str(data.get("scope", "asthma_or_unclear")).strip().lower()
    if scope not in ("asthma_or_unclear", "other_condition", "off_topic"):
        scope = "asthma_or_unclear"

    enough = data.get("enough", True)
    if isinstance(enough, str):
        enough = enough.strip().lower() == "true"
    question = (data.get("question") or "").strip()
    if not enough and scope == "asthma_or_unclear":
        if not question:
            question = DEFAULT_QUESTION
        if not question.endswith("?"):
            question = question.rstrip(". ") + "?"
    return {"scope": scope, "enough": bool(enough), "question": question}


def count_recent_clarifications(messages) -> int:
    """How many AI follow-up questions in a row (most recent) without a real answer."""
    count = 0
    for m in reversed(messages):
        if m.role != "ai":
            continue
        if (m.content or "").strip().endswith("?"):
            count += 1
        else:
            break
    return count


# ---------------------------------------------------------------- endpoints
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    user_query = (request.query or "").strip()

    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        db.add(User(id=request.user_id, username=f"user_{request.user_id}", role="patient"))
        db.commit()

    if not user_query:
        result = make_result("clarify", question="Please describe what you are experiencing.")
        result["response"] = build_plain_text(result)
        return result

    # Recent history (memory)
    recent = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == request.user_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(6)
        .all()
    )
    recent.reverse()
    history_text = "\n".join(
        f"{'Patient' if m.role == 'user' else 'Assistant'}: {m.content}" for m in recent[-4:]
    )

    # 1. Emergency red flags (checked on what the user actually typed)
    if is_emergency(user_query):
        result = make_result("emergency", answer=EMERGENCY_MESSAGE)
    else:
        memory_query = reformulate_query(history_text, user_query, fast_llm) if history_text else user_query

        # 2. Guardrails
        safe, guard_response = guard.filter_query(memory_query)
        if not safe:
            result = make_result("blocked", answer=guard_response)
        else:
            # 3. Triage (skipped after MAX_CLARIFY follow-ups so it never loops)
            triage = {"scope": "asthma_or_unclear", "enough": True, "question": ""}
            if count_recent_clarifications(recent) < MAX_CLARIFY:
                triage = triage_query(memory_query, fast_llm)

            if triage.get("scope") == "other_condition":
                result = make_result("no_match", answer=SCOPE_MESSAGE)
            elif not triage["enough"]:
                result = make_result("clarify", question=triage["question"])
            else:
                # 4. Retrieval + grounded answer + faithfulness check
                result = rag_system.run(memory_query)

    result["response"] = build_plain_text(result)

    # Save conversation
    ai_text = result["question"] if result["status"] == "clarify" else result["answer"]
    db.add(ChatMessage(user_id=request.user_id, role="user", content=user_query))
    db.add(ChatMessage(user_id=request.user_id, role="ai", content=ai_text))
    db.commit()

    return result


@app.get("/api/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.timestamp)
        .all()
    )
    return [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in messages]


@app.delete("/api/history/{user_id}")
def clear_history(user_id: int, db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
    db.commit()
    return {"status": "cleared"}
