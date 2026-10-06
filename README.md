# GitContext

**Ask questions about any GitHub repository.** GitContext indexes source code, docs and commit history, then retrieves the most relevant pieces using hybrid search (semantic + keyword) with cross-encoder reranking (RAG).

> Status: phases 1-5 done. LLM answers with citations, API/UI and evaluation are next.

## Quick start
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1       # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli index https://github.com/pallets/flask
python -m app.cli search "how does request routing work?"
python -m app.cli search "dispatch_request" --mode bm25
pytest
```

## Retrieval modes
| Mode | What it does | Best for |
|------|--------------|----------|
| `vector` | embedding similarity | natural-language questions |
| `bm25` | keyword match (code-aware tokenizer) | exact function names, error text |
| `hybrid` | vector + BM25 merged with Reciprocal Rank Fusion | general use |
| `rerank` (default) | hybrid, then cross-encoder re-sorts top 30 | highest quality |

## How it works
1. **Ingest**: clone repo, read `.py`/`.md` files + git history
2. **Chunk**: split Python by function/class (AST), docs by heading
3. **Embed**: `bge-small-en-v1.5` (local, free) stored in Qdrant with metadata
4. **Retrieve**: vector + BM25 -> RRF fusion -> cross-encoder rerank

## Roadmap
- [x] Ingestion, chunking, embeddings, vector search
- [x] BM25 + hybrid retrieval (RRF) + reranking
- [ ] LLM answers with citations
- [ ] FastAPI backend + UI
- [ ] Evaluation (Recall@5, latency) and results table
