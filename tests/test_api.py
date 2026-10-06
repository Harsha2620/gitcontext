import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

import app.api as api  # noqa: E402

CHUNK = {"id": "1", "kind": "function", "path": "src/app.py", "name": "dispatch",
         "start_line": 1, "end_line": 5, "text": "def dispatch(): pass", "score": 0.9,
         "commit": "abc12345def", "author": "dev", "last_modified": "2026-01-01"}


def test_ask_returns_answer_and_marks_cited_sources(monkeypatch):
    fake = {"answer": "It dispatches [1].", "cited": [1], "invalid_citations": [],
            "sources": [CHUNK], "retrieval_ms": 5.0, "total_ms": 9.0}
    monkeypatch.setattr(api, "answer", lambda q, k, m, retrieve_fn=None: fake)
    r = TestClient(api.app).post("/ask", json={"question": "how does it work"})
    assert r.status_code == 200
    assert r.json()["sources"][0]["cited"] is True


def test_short_question_is_rejected():
    assert TestClient(api.app).post("/ask", json={"question": "hi"}).status_code == 422
