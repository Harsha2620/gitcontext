"""Phase 7: FastAPI backend + web UI.   Run: python -m uvicorn app.api:app --port 8000"""
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.limits import RateLimiter
from app.llm import answer, source_label

DISABLE_RERANK = os.getenv("DISABLE_RERANK") == "1"  # the cross-encoder needs PyTorch (too big for 512 MB)
limiter = RateLimiter()  # protects the free LLM quota on a public demo
_lock = threading.Lock()  # local Qdrant + models handle one retrieval at a time


class Query(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(5, ge=1, le=10)
    mode: Literal["vector", "bm25", "hybrid", "rerank"] = "vector"


def _check_mode(q: "Query") -> None:
    if DISABLE_RERANK and q.mode == "rerank":
        raise HTTPException(400, "Reranking is turned off in the hosted demo (memory limit). Use vector or hybrid.")


def _locked_retrieve(question: str, k: int, mode: str) -> list[dict]:
    from app.retrieval import retrieve
    with _lock:
        return retrieve(question, k, mode)


def _source(n: int, c: dict, cited: list[int]) -> dict:
    return {"n": n, "label": source_label(c), "kind": c["kind"], "path": c["path"],
            "author": c["author"], "date": c["last_modified"][:10],
            "score": round(c["score"], 3), "snippet": c["text"][:700], "cited": n in cited}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _locked_retrieve("warm up", 1, "vector" if DISABLE_RERANK else "rerank")  # load all models once at startup
    except Exception as e:
        print(f"Warm-up skipped: {e}")
    yield


app = FastAPI(title="GitContext", lifespan=lifespan)


@app.get("/")
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    from app.retrieval import _load_chunks
    return {"status": "ok", "chunks": len(_load_chunks()), "rerank": not DISABLE_RERANK}


@app.post("/search")
def search(q: Query):
    _check_mode(q)
    start = time.perf_counter()
    results = _locked_retrieve(q.question, q.k, q.mode)
    return {"retrieval_ms": round((time.perf_counter() - start) * 1000),
            "sources": [_source(i, c, []) for i, c in enumerate(results, 1)]}


@app.post("/ask")
def ask(q: Query, request: Request):
    _check_mode(q)
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown")
    problem = limiter.check(ip)
    if problem:
        raise HTTPException(429, problem)
    try:
        res = answer(q.question, q.k, q.mode, retrieve_fn=_locked_retrieve)
    except RuntimeError as e:  # e.g. missing API key
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"LLM request failed: {e}")
    return {"answer": res["answer"], "cited": res["cited"],
            "invalid_citations": res["invalid_citations"],
            "sources": [_source(i, c, res["cited"]) for i, c in enumerate(res["sources"], 1)],
            "retrieval_ms": round(res["retrieval_ms"]), "total_ms": round(res["total_ms"])}
