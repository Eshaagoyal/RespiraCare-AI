# RespiraCare AI (Asthma Edition)

An asthma information assistant. It asks a follow-up question when a message is vague, answers only from retrieved passages of trusted sources (WHO, NHS, NHLBI, MedlinePlus), shows its sources, checks its answer against them, and says so when it cannot answer. It also detects emergency danger signs. It gives general information, not a diagnosis.

Stack: React (Vite, Tailwind), FastAPI, SQLite, FAISS + BM25 + TF-IDF (Reciprocal Rank Fusion, query expansion, HyDE), Groq-hosted language models.

## Run
1. python -m venv venv, activate it, then pip install -r requirements.txt
2. Create a file named .env with one line: GROQ_API_KEY=your_key
3. python ingest_kb.py        (builds the index from data/kb/kb_clean.csv)
4. uvicorn api:app --reload   (API docs at http://127.0.0.1:8000/docs)
5. cd frontend, npm install, npm run dev   (http://localhost:5173)
6. python run_eval.py          (runs the 25 edge-case tests, writes eval_results.md)

## Limitations
Asthma only, English only, 42 knowledge chunks, no content for children, no medicine doses. Emergency detection is rule-based and can miss unusual wording. Answers take 5 to 30 seconds. Not medical advice.