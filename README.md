# GitContext

**Ask questions about any GitHub repository.** GitContext indexes source code, docs and commit history, retrieves the best context with hybrid search (semantic + keyword) and cross-encoder reranking, then answers with an LLM that **cites its sources**.

> Status: phases 1-6 done. API/UI, freshness (re-indexing) and evaluation are next.

## Quick start
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1       # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # then paste your free Groq key into .env
python -m app.cli index https://github.com/pallets/flask
python -m app.cli ask "How does Flask match a URL to a view function?"
pytest
```

## Commands
| Command | What it does |
|---------|--------------|
| `index <repo-url>` | clone, chunk, embed and store a repo |
| `search "<q>" --mode vector\|bm25\|hybrid\|rerank` | retrieval only (see modes below) |
| `ask "<q>"` | retrieval + LLM answer with `[n]` citations |

## Retrieval modes
| Mode | What it does | Best for |
|------|--------------|----------|
| `vector` | embedding similarity | natural-language questions |
| `bm25` | keyword match (code-aware tokenizer) | exact function names, error text |
| `hybrid` | vector + BM25 merged with Reciprocal Rank Fusion | general use |
| `rerank` (default) | hybrid, then cross-encoder re-sorts top 30 | highest quality |

## Grounded answers
- The LLM may only use the retrieved sources and must cite them as `[1]`, `[2]`...
- If the sources do not contain the answer it replies "I don't know based on the indexed repository."
- Citations are validated: references to non-existent sources are flagged.
- Works with any OpenAI-compatible API (Groq free tier by default, set in `.env`).

## How it works
1. **Ingest**: clone repo, read `.py`/`.md` files + git history
2. **Chunk**: split Python by function/class (AST), docs by heading
3. **Embed**: `bge-small-en-v1.5` (local, free) stored in Qdrant with metadata
4. **Retrieve**: vector + BM25 -> RRF fusion -> cross-encoder rerank
5. **Answer**: LLM answers from numbered sources with citations

## Roadmap
- [x] Ingestion, chunking, embeddings, vector search
- [x] BM25 + hybrid retrieval (RRF) + reranking
- [x] LLM answers with citations
- [ ] FastAPI backend + UI
- [ ] Auto re-index changed files
- [ ] Evaluation (Recall@5, latency) and results table
