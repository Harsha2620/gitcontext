# GitContext

**Ask questions about any GitHub repository.** GitContext indexes source code, docs and commit history, then retrieves the most relevant pieces with semantic search (RAG).

> Status: phases 1-4 done (ingestion, smart chunking, embeddings, vector search). Hybrid retrieval, reranking, LLM answers, API and evaluation are next.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli index https://github.com/pallets/flask
python -m app.cli search "how does request routing work?"
pytest
```

## How it works
1. **Ingest**: clone repo, read `.py`/`.md` files + git history
2. **Chunk**: split Python by function/class (AST), docs by heading
3. **Embed**: `bge-small-en-v1.5` (runs locally, free)
4. **Store/search**: Qdrant with metadata (path, author, commit, date)

## Roadmap
- [x] Ingestion, chunking, embeddings, vector search
- [ ] BM25 + hybrid retrieval, reranking
- [ ] LLM answers with citations
- [ ] FastAPI backend + UI
- [ ] Evaluation (Recall@5, latency) and results table
