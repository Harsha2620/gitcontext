from app.llm import NO_ANSWER, answer, build_prompt, extract_citations

CHUNK = {
    "id": "1", "kind": "function", "path": "src/app.py", "name": "dispatch",
    "start_line": 10, "end_line": 20, "text": "def dispatch(): pass",
    "commit": "abc12345def", "author": "dev", "last_modified": "2026-01-01",
}


def test_build_prompt_numbers_sources():
    prompt = build_prompt("how?", [CHUNK, CHUNK])
    assert "[1] src/app.py:10-20" in prompt and "[2] src/app.py:10-20" in prompt
    assert prompt.endswith("Question: how?")


def test_extract_citations_valid_invalid_and_comma_form():
    valid, invalid = extract_citations("It routes [1][2]. Also [1, 3] and [9].", 3)
    assert valid == [1, 2, 3] and invalid == [9]


def test_answer_with_fake_llm_tracks_citations():
    res = answer("q", retrieve_fn=lambda q, k, m: [CHUNK, CHUNK],
                 complete_fn=lambda s, u: "It dispatches requests [2].")
    assert res["cited"] == [2] and res["invalid_citations"] == []


def test_answer_without_context_skips_llm():
    def boom(s, u):
        raise AssertionError("LLM should not be called")
    res = answer("q", retrieve_fn=lambda q, k, m: [], complete_fn=boom)
    assert res["answer"] == NO_ANSWER
