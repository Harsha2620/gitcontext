import pytest

from app.retrieval import rrf_fuse, tokenize


def test_tokenize_keeps_whole_and_parts():
    t = tokenize("dispatch_request")
    assert "dispatch_request" in t and "dispatch" in t and "request" in t


def test_tokenize_splits_camel_case():
    t = tokenize("getUserName")
    assert "get" in t and "user" in t and "name" in t


def test_rrf_prefers_items_in_both_lists():
    fused = [i for i, _ in rrf_fuse([["a", "b", "c"], ["c", "b", "d"]])]
    assert set(fused[:2]) == {"b", "c"}
    assert set(fused[2:]) == {"a", "d"}


def test_bm25_finds_exact_function_name():
    pytest.importorskip("rank_bm25")
    from app.retrieval import BM25Index
    chunks = [
        {"id": "1", "text": "def dispatch_request(self): route the request"},
        {"id": "2", "text": "def load_config(path): read a settings file"},
        {"id": "3", "text": "class Logger: writes messages to disk"},
    ]
    assert BM25Index(chunks).search("dispatch_request", k=1)[0]["id"] == "1"
