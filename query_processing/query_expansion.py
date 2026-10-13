import re


class MultiQueryExpander:

    def __init__(self, llm):

        self.llm = llm

    def expand(self, query):

        prompt = f"""You are helping a medical search system retrieve information about asthma.

Given a user question, write 5 different search queries that could help find relevant
medical documents. Use synonyms, medical terminology, alternative phrasing and related terms.
Do not add facts that are not in the question.

Reply with ONLY the queries, one per line. No numbering, no bullets, no introduction.

User question:
{query}
"""

        try:
            response = self.llm.invoke(prompt)
            lines = (response.content or "").split("\n")
        except Exception as e:
            print(f"[query expansion] failed: {e}")
            return []

        queries = []

        for line in lines:

            q = re.sub(r"^\s*(?:[-*\u2022]|\d+[.)])\s*", "", line).strip().strip('"')

            # skip empty lines, one-word lines and any introduction such as "Here are 5 queries:"
            if len(q.split()) < 2 or q.endswith(":") or len(q) > 200:
                continue

            queries.append(q)

        return queries[:5]
