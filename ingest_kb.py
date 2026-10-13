"""
ingest_kb.py - build the FAISS index from the clean asthma knowledge base.

Put this file in the project root (next to api.py) and run:   python ingest_kb.py

What it does
  - reads ONLY data/kb/kb_clean.csv (no PDFs, no patient-record CSV)
  - one chunk = one document (no re-chunking), with the metadata the app needs for
    citations: title, source, source_url, category, chunk_id
  - renames the old vector_db folder to vector_db_old (it never deletes anything)
  - saves the new index to vector_db and runs three test searches

Stop the backend (uvicorn) before running, because Windows locks the old index files.
Use  python ingest_kb.py --dry-run  to check the CSV without building anything.
"""
import os
import sys
import time

import pandas as pd
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(BASE_DIR, "data", "kb", "kb_clean.csv")
INDEX_DIR = os.path.join(BASE_DIR, "vector_db")

REQUIRED = ["chunk_id", "condition", "category", "title", "content", "source", "source_url", "source_type"]


def load_kb_documents(path=KB_PATH):
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SystemExit(f"{path} is missing columns: {missing}")

    df = df.dropna(subset=["title", "content"])
    df = df[df["condition"].str.lower() == "asthma"]
    df = df.drop_duplicates(subset=["content"])

    docs = []
    for _, r in df.iterrows():
        metadata = {
            "chunk_id": str(r["chunk_id"]),
            "condition": str(r["condition"]),
            "category": str(r["category"]),
            "title": str(r["title"]),
            "source": str(r["source"]),
            "source_url": str(r["source_url"]),
            "source_type": str(r["source_type"]),
            "audience": str(r["audience"]) if "audience" in df.columns else "adult",
        }
        # the title is part of the searchable text, so lists like "What to do" keep their context
        docs.append(Document(page_content=f"{r['title']}\n{r['content']}", metadata=metadata))
    return docs


def print_summary(docs):
    words = [len(d.page_content.split()) for d in docs]
    by_source, by_category = {}, {}
    for d in docs:
        by_source[d.metadata["source"]] = by_source.get(d.metadata["source"], 0) + 1
        by_category[d.metadata["category"]] = by_category.get(d.metadata["category"], 0) + 1
    print(f"chunks: {len(docs)}   words per chunk: min {min(words)}, max {max(words)}")
    print("per source  :", by_source)
    print("per category:", by_category)


def main():
    dry_run = "--dry-run" in sys.argv
    docs = load_kb_documents()
    if not docs:
        raise SystemExit("No chunks loaded. Check data/kb/kb_clean.csv")
    print_summary(docs)
    if dry_run:
        print("\nDry run only: nothing was built.")
        return

    # import here so --dry-run works without the heavy libraries
    from langchain_community.vectorstores import FAISS
    from ingestion.embedding import load_embeddings

    # back up the old index instead of deleting it
    if os.path.isdir(INDEX_DIR):
        backup = os.path.join(BASE_DIR, "vector_db_old")
        if os.path.exists(backup):
            backup = os.path.join(BASE_DIR, "vector_db_old_" + time.strftime("%Y%m%d_%H%M%S"))
        try:
            os.rename(INDEX_DIR, backup)
        except PermissionError:
            raise SystemExit(
                "Cannot rename vector_db. Stop the backend (Ctrl+C in the uvicorn terminal) and run again."
            )
        print(f"\nOld index kept as: {os.path.basename(backup)}")

    print("\nLoading embedding model...")
    embeddings = load_embeddings()

    print("Building FAISS index...")
    vector_db = FAISS.from_documents(docs, embeddings)
    vector_db.save_local(INDEX_DIR)

    count = vector_db.index.ntotal
    print(f"\nSaved {count} vectors to vector_db (expected {len(docs)})")
    if count != len(docs):
        print("WARNING: vector count does not match the number of chunks")

    print("\nTest searches:")
    for q in ["wheezing and coughing at night", "when should I go to the emergency room", "can asthma be cured"]:
        print(f"\n  Q: {q}")
        for d in vector_db.similarity_search(q, k=3):
            print(f"     - [{d.metadata['source']}] {d.metadata['title']} ({d.metadata['category']})")
    print("\nDone. Start the backend again.")


if __name__ == "__main__":
    main()
