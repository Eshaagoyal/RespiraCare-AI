from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class TFIDFRetriever:

    def __init__(self, documents):

        self.documents = documents

        self.texts = [
            doc.page_content for doc in documents
        ]

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True
        )

        self.matrix = self.vectorizer.fit_transform(self.texts)

        print("TF-IDF index created.")

    def search(self, query, k=5):

        query_vector = self.vectorizer.transform([query])

        scores = (self.matrix @ query_vector.T).toarray().ravel()

        ranked_indices = np.argsort(scores)[::-1][:k]

        # keep only chunks that share at least one word with the query
        return [self.documents[i] for i in ranked_indices if scores[i] > 0]
