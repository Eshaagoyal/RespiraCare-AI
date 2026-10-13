import re

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


def tokenize(text):
    """Lower-case words only, without punctuation or common stop words.

    The old version split on spaces, so "wheezing," (with a comma) never matched "wheezing".
    """
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [w for w in words if w not in ENGLISH_STOP_WORDS]


class BM25Retriever:

    def __init__(self, documents):

        self.documents = documents

        self.corpus = [tokenize(doc.page_content) for doc in documents]

        self.bm25 = BM25Okapi(self.corpus)

        print("BM25 index created.")

    def search(self, query, k=5):

        tokens = tokenize(query)

        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:k]

        # keep only chunks that share at least one word with the query
        return [self.documents[i] for i in ranked_indices if scores[i] > 0]
