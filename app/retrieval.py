"""Phase 5: keyword search (BM25) + hybrid fusion (RRF) + reranking.

Modes:
  vector  - meaning-based search only (phase 4)
  bm25    - keyword search only (great for exact function names / error text)
  hybrid  - vector + bm25 merged with Reciprocal Rank Fusion
  rerank  - hybrid, then a cross-encoder re-sorts the best candidates (slowest)
"""
import json
import re

from app.config import CHUNKS_PATH, RERANK_MODEL

_WORD = re.compile(r"[A-Za-z0-9_]+")
_CAMEL = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+")


def tokenize(text: str) -> list[str]:
    """Code-aware tokens: keep 'dispatch_request' AND its parts 'dispatch', 'request'.
    Also splits camelCase: 'getUserName' -> 'get', 'user', 'name'."""
    tokens = []
    for word in _WORD.findall(text):
        tokens.append(word.lower())
        parts = []
        for seg in word.split("_"):
            parts.extend(p.lower() for p in _CAMEL.findall(seg))
        if len(parts) > 1:
            tokens.extend(parts)
    return tokens


def rrf_fuse(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion: items ranked high in several lists win."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class BM25Index:
    def __init__(self, chunks: list[dict]):
        from rank_bm25 import BM25Okapi
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])

    def search(self, question: str, k: int = 5) -> list[dict]:
        scores = self.bm25.get_scores(tokenize(question))
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in top if scores[i] > 0]


_cache: dict = {}


def _load_chunks() -> list[dict]:
    if CHUNKS_PATH.exists():
        return json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    from app.indexing import dump_chunks  # first run after upgrading: no re-index needed
    return dump_chunks()


def _bm25() -> BM25Index:
    if "bm25" not in _cache:
        _cache["bm25"] = BM25Index(_load_chunks())
    return _cache["bm25"]


def rerank(question: str, candidates: list[dict]) -> list[dict]:
    if "reranker" not in _cache:
        from sentence_transformers import CrossEncoder
        _cache["reranker"] = CrossEncoder(RERANK_MODEL, max_length=512)
    scores = _cache["reranker"].predict([(question, c["text"]) for c in candidates])
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [{**c, "score": float(s)} for c, s in ranked]


def retrieve(question: str, k: int = 5, mode: str = "vector", pool: int = 30) -> list[dict]:
    from app.indexing import search as vector_search
    if mode == "vector":
        return vector_search(question, k)
    if mode == "bm25":
        return _bm25().search(question, k)

    vec = vector_search(question, pool)
    kw = _bm25().search(question, pool)
    by_id = {r["id"]: r for r in vec + kw}
    fused = rrf_fuse([[r["id"] for r in vec], [r["id"] for r in kw]])
    candidates = [{**by_id[i], "score": s} for i, s in fused[:pool]]
    if mode == "hybrid":
        return candidates[:k]
    return rerank(question, candidates)[:k]
