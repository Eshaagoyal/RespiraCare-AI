from retrieval.hybrid_search import reciprocal_rank_fusion


class RetrievalPipeline:

    def __init__(self, query_pipeline, hybrid_retriever):

        self.query_pipeline = query_pipeline
        self.hybrid_retriever = hybrid_retriever


    def reciprocal_rank_fusion(self, results, k=60):

        return reciprocal_rank_fusion(results, k)


    def retrieve(self, query, top_k=10):

        query_data = self.query_pipeline.process(query)

        queries = query_data["all_queries"]
        hyde_vector = query_data["hyde_vector"]

        results = []

        # Hybrid retrieval (BM25 + TF-IDF + FAISS) for the original and expanded queries
        for q in queries[:6]:

            results.append(self.hybrid_retriever.search(q))

        # HyDE: semantic search with the hypothetical answer (skipped if it could not be made)
        if hyde_vector is not None:

            results.append(self.hybrid_retriever.vector_search(hyde_vector))

        # Rank fusion
        fused_docs = self.reciprocal_rank_fusion(results)

        return fused_docs[:top_k]
