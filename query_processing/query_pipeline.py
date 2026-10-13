class QueryPipeline:

    def __init__(self, tokenizer, bigram_model, multiquery_expander, hyde_generator):

        self.tokenizer = tokenizer
        self.bigram = bigram_model
        self.multiquery = multiquery_expander
        self.hyde = hyde_generator

    def process(self, query):

        tokens = self.tokenizer.tokenize(query)

        bigram_suggestions = []

        for token in tokens:
            suggestions = self.bigram.suggest(token)
            bigram_suggestions.extend(suggestions)

        bigram_suggestions = list(dict.fromkeys(bigram_suggestions))

        expanded_queries = self.multiquery.expand(query)

        # the original query always comes first; duplicates are removed but the order is kept
        all_queries = list(dict.fromkeys([query] + expanded_queries))

        hyde_vector = self.hyde.generate_vector(query)

        return {
            "tokens": tokens,
            "bigram_suggestions": bigram_suggestions,
            "expanded_queries": expanded_queries,
            "all_queries": all_queries,
            "hyde_vector": hyde_vector
        }
