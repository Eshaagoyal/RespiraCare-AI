import os

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from safety.guardrails import Guardrails

# Query processing
from query_processing.tokenization import Tokenizer
from query_processing.bigram_model import BigramModel
from query_processing.query_expansion import MultiQueryExpander
from query_processing.hyde import HydeGenerator
from query_processing.query_pipeline import QueryPipeline

# Retrieval modules
from retrieval.vector_search import load_vector_store
from retrieval.bm25_search import BM25Retriever
from retrieval.tfidf_search import TFIDFRetriever
from retrieval.hybrid_search import HybridRetriever
from retrieval.retrieval_pipeline import RetrievalPipeline

# RAG pipeline
from rag.rag_chain import RAGPipeline

# The API key is read from a file named .env in the project folder (never write it in code):
#   GROQ_API_KEY=your_key_here
load_dotenv()

MAIN_MODEL = os.getenv("MAIN_MODEL", "openai/gpt-oss-120b")   # writes and checks the answer
FAST_MODEL = os.getenv("FAST_MODEL", "openai/gpt-oss-20b")    # triage, query expansion, HyDE, memory


def _make_llm(model, key, temperature):
    return ChatGroq(model_name=model, groq_api_key=key, temperature=temperature)


def initialize_system():

    print("Initializing Asthma RAG System...\n")

    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Create a file named .env in the project folder "
            "with one line:  GROQ_API_KEY=your_key_here"
        )

    # Embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Groq language models
    llm = _make_llm(MAIN_MODEL, key, 0.2)        # answer generation
    judge_llm = _make_llm(MAIN_MODEL, key, 0.0)  # faithfulness check
    fast_llm = _make_llm(FAST_MODEL, key, 0.0)   # small helper tasks

    try:
        fast_llm.invoke("Reply with OK")
    except Exception as e:
        print(f"[warning] fast model {FAST_MODEL} is not available ({e}). Using {MAIN_MODEL} for everything.")
        fast_llm = llm

    # Load vector database
    vector_db = load_vector_store(embeddings)

    # All stored chunks, for the keyword retrievers
    try:
        documents = list(vector_db.docstore._dict.values())
    except Exception:
        documents = vector_db.similarity_search("", k=1000)
    print(f"Knowledge base: {len(documents)} chunks")

    # Keyword retrievers
    bm25_retriever = BM25Retriever(documents)
    tfidf_retriever = TFIDFRetriever(documents)

    # Hybrid retriever
    hybrid_retriever = HybridRetriever(
        vector_db,
        bm25_retriever,
        tfidf_retriever
    )

    # Query intelligence
    tokenizer = Tokenizer()
    bigram_model = BigramModel()
    multiquery = MultiQueryExpander(fast_llm)
    hyde = HydeGenerator(fast_llm, embeddings)

    query_pipeline = QueryPipeline(
        tokenizer,
        bigram_model,
        multiquery,
        hyde
    )

    # Retrieval pipeline
    retrieval_pipeline = RetrievalPipeline(
        query_pipeline,
        hybrid_retriever
    )

    # RAG pipeline
    rag = RAGPipeline(
        retrieval_pipeline,
        llm,
        judge_llm
    )
    rag.fast_llm = fast_llm  # used by api.py for triage and chat memory

    print("System Ready!\n")

    return rag


def main():
    """Simple command-line chat for quick tests: python ai_core.py"""

    rag = initialize_system()
    guard = Guardrails()

    print("Asthma Medical AI Assistant")
    print("Type 'exit' to quit.\n")

    while True:

        query = input("Ask a question: ")

        if query.lower() == "exit":
            break

        safe, response = guard.filter_query(query)

        if not safe:
            print("\n" + response + "\n---------------------------\n")
            continue

        result = rag.run(query)

        print("\n" + (result.get("answer") or "") + "\n")
        for i, c in enumerate(result.get("citations", []), start=1):
            print(f"[{i}] {c['source']}: {c['title']} ({c['url']})")
        print("\n---------------------------\n")


if __name__ == "__main__":
    main()
