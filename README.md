# GitContext

**Ask questions about any GitHub repository.** GitContext indexes source code, docs and commit history, retrieves the best context with hybrid search (semantic + keyword) and cross-encoder reranking, then answers with an LLM that **cites its sources**.

> Status: phases 1-8 done. Freshness (re-indexing) and evaluation are next.

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

## Web UI + API
```bash
python -m uvicorn app.api:app --port 8000   # stop it (Ctrl+C) before re-indexing
```
Open http://localhost:8000 for the UI, or http://localhost:8000/docs for the API.
Endpoints: `POST /ask`, `POST /search`, `GET /health`. Models load once at startup, so queries are fast.

## Commands
| Command | What it does |
|---------|--------------|
| `index <repo-url>` | clone, chunk, embed and store a repo |
| `search "<q>" --mode vector\|bm25\|hybrid\|rerank` | retrieval only (see modes below) |
| `ask "<q>"` | retrieval + LLM answer with `[n]` citations |

## Retrieval modes
| Mode | What it does | Best for |
|------|--------------|----------|
| `vector` (default) | embedding similarity | natural-language questions, identifiers |
| `bm25` | keyword match (code-aware tokenizer) | exact function names, error text |
| `hybrid` | vector + BM25 merged with Reciprocal Rank Fusion | general use |
| `rerank` | hybrid, then cross-encoder re-sorts top 30 | slowest; no overall gain in our benchmark |

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
- [x] FastAPI backend + web UI
- [ ] Auto re-index changed files
- [x] Evaluation (Recall@5, MRR, latency) -> see below

## Evaluation
`python -m eval.run_eval` runs ~44 labelled questions (natural language, exact identifiers, docs)
against every retrieval mode and writes `eval/results.md`. A result is correct when a retrieved chunk
matches the expected function/class name or file path. Add `--answers 10` to also measure citation
accuracy and refusal on out-of-scope questions.

**Results** (Flask repo, 43 labelled questions, k=5, laptop CPU, retrieval only, rerank pool 15):

| Mode | Recall@1 | Recall@5 | MRR | Precision@5 | p50 latency | p95 latency |
|---|---|---|---|---|---|---|
| vector | 67% | 86% | 0.75 | 32% | 65 ms | 76 ms |
| bm25 | 37% | 77% | 0.53 | 24% | 4 ms | 5 ms |
| hybrid | 60% | 84% | 0.69 | 32% | 31 ms | 84 ms |
| rerank | 60% | 86% | 0.70 | 32% | 1253 ms | 1410 ms |

Recall@5 by question type (vector / bm25 / hybrid / rerank): natural (25) 92 / 80 / 88 / 88%,
identifiers (10) 100 / 90 / 100 / 100%, docs how-to (8) 50 / 50 / 50 / 62%.

**Findings**
- Dense retrieval alone matched or beat hybrid and reranking on this benchmark, at a fraction of the latency,
  so it is the default. Hybrid and rerank remain selectable.
- BM25 alone is the weakest (it misses paraphrased questions) but is near-instant.
- The general-purpose MS MARCO cross-encoder added ~1.2 s per query with no overall accuracy gain.
- Documentation how-to questions are the weak spot (50-62%): the top results are often source code rather than the docs page.

**Limitations:** 43 questions (one question = 2.3 points), labels written by me before running the evaluation,
latency varies between runs on a laptop. Commit-history and error-message queries are not covered yet.
