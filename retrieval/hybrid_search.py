from collections import defaultdict


def reciprocal_rank_fusion(result_lists, k=60):
    """Merge several ranked lists of documents into one (Reciprocal Rank Fusion)."""

    scores = defaultdict(float)
    doc_map = {}

    for docs in result_lists:

        for rank, doc in enumerate(docs):

            key = doc.page_content

            scores[key] += 1.0 / (k + rank + 1)

            doc_map[key] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [doc_map[key] for key, _ in ranked]


class HybridRetriever:

    def __init__(self, vector_db, bm25_retriever, tfidf_retriever):

        self.vector_db = vector_db
        self.bm25 = bm25_retriever
        self.tfidf = tfidf_retriever

        print("Hybrid Retriever initialized.")


    def vector_search(self, query_vector, k=10):
        """
        Semantic search using FAISS vector DB
        """

        docs = self.vector_db.similarity_search_by_vector(
            query_vector,
            k=k
        )

        return docs


    def search(self, query, k=10):
        """
        Hybrid retrieval: BM25 + TF-IDF + FAISS, merged with Reciprocal Rank Fusion.

        The old version simply joined the three lists and cut it at k, so BM25 filled
        every slot and the other two methods never made it into the result.
        """

        bm25_docs = self.bm25.search(query, k)
        tfidf_docs = self.tfidf.search(query, k)
        vector_docs = self.vector_db.similarity_search(query, k)

        return reciprocal_rank_fusion([bm25_docs, tfidf_docs, vector_docs])[:k]
