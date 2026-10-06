"""Phase 6: answer questions from retrieved chunks, with [n] source citations.

Works with any OpenAI-compatible API (Groq, OpenAI, Gemini, Ollama...).
Configure it in .env (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL).
"""
import os
import re
import time

NO_ANSWER = "I don't know based on the indexed repository."
MAX_CHARS_PER_SOURCE = 2000

SYSTEM_PROMPT = f"""You are GitContext, an assistant that answers questions about a software repository.
Rules:
1. Use ONLY the numbered sources provided. Do not use outside knowledge.
2. After every claim, cite the source number like [1] or [2][3].
3. If the sources do not contain the answer, reply exactly: {NO_ANSWER}
4. Be concise. Use short paragraphs or bullet points. Show code only when it helps."""


def source_label(c: dict) -> str:
    """Human-readable location of a chunk: file:lines, or commit info."""
    if c.get("kind") == "commit":
        return f"commit {c['commit'][:8]} by {c['author']} ({c['last_modified'][:10]})"
    lines = f":{c['start_line']}-{c['end_line']}" if c.get("start_line") else ""
    return f"{c['path']}{lines}"


def build_prompt(question: str, chunks: list[dict]) -> str:
    blocks = [
        f"[{i}] {source_label(c)}\n{c['text'][:MAX_CHARS_PER_SOURCE]}"
        for i, c in enumerate(chunks, start=1)
    ]
    return "Sources:\n\n" + "\n\n---\n\n".join(blocks) + f"\n\nQuestion: {question}"


def extract_citations(answer: str, n_sources: int) -> tuple[list[int], list[int]]:
    """Return (valid_citations, invalid_citations) found like [1], [2][3] or [1, 2]."""
    found: set[int] = set()
    for group in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", answer):
        found.update(int(n) for n in re.split(r"\s*,\s*", group))
    valid = sorted(n for n in found if 1 <= n <= n_sources)
    invalid = sorted(n for n in found if not 1 <= n <= n_sources)
    return valid, invalid


def llm_complete(system: str, user: str) -> str:
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise RuntimeError("LLM_API_KEY is missing. Copy .env.example to .env and paste your key.")
    client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"))
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
        max_tokens=700,
    )
    return resp.choices[0].message.content.strip()


def answer(question: str, k: int = 5, mode: str = "rerank",
           retrieve_fn=None, complete_fn=None) -> dict:
    """Retrieve context, ask the LLM, and return answer + sources + timings.
    retrieve_fn / complete_fn can be swapped out (used by tests)."""
    if retrieve_fn is None:
        from app.retrieval import retrieve as retrieve_fn
    complete_fn = complete_fn or llm_complete

    t0 = time.perf_counter()
    chunks = retrieve_fn(question, k, mode)
    t1 = time.perf_counter()
    result = {"sources": chunks, "cited": [], "invalid_citations": [],
              "retrieval_ms": (t1 - t0) * 1000}

    if not chunks:
        result.update(answer=NO_ANSWER, total_ms=result["retrieval_ms"])
        return result

    text = complete_fn(SYSTEM_PROMPT, build_prompt(question, chunks))
    result["answer"] = text
    result["cited"], result["invalid_citations"] = extract_citations(text, len(chunks))
    result["total_ms"] = (time.perf_counter() - t0) * 1000
    return result
