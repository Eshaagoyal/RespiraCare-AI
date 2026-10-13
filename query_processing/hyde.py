class HydeGenerator:

    def __init__(self, llm, embeddings):

        self.llm = llm
        self.embeddings = embeddings

    def generate_vector(self, query):
        """Write a short hypothetical answer and return its embedding (None if it fails)."""

        prompt = f"""You are a medical expert.

Write a short factual paragraph answering the following asthma-related question.

Question:
{query}

Use medical terminology when possible.
"""

        try:
            response = self.llm.invoke(prompt)

            hypothetical_doc = response.content

            if not hypothetical_doc or not hypothetical_doc.strip():
                return None

            return self.embeddings.embed_query(hypothetical_doc)

        except Exception as e:
            print(f"[HyDE] failed: {e}")
            return None
