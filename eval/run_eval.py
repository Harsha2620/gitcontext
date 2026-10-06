"""Phase 8: measure retrieval quality and speed on a labelled question set.

  python -m eval.run_eval                 # retrieval metrics for all 4 modes
  python -m eval.run_eval --pool 15       # rerank fewer candidates (faster)
  python -m eval.run_eval --answers 10    # also test LLM answers (slow, uses API quota)

Stop the web server first (Ctrl+C): only one program can open the local database.
"""
import argparse
import json
import statistics
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
MODES = ["vector", "bm25", "hybrid", "rerank"]


def is_relevant(chunk: dict, q: dict) -> bool:
    """A chunk is correct if its function/class name or its file path matches the label."""
    name = chunk.get("name", "")
    if any(name == n or name.endswith("." + n) for n in q.get("names", [])):
        return True
    return any(p in chunk.get("path", "") for p in q.get("paths", []))


def compute_metrics(rows: list[dict]) -> dict:
    n = len(rows)
    ms = sorted(r["ms"] for r in rows)
    return {
        "recall_1": sum(r["hit1"] for r in rows) / n,
        "recall_k": sum(r["hit"] for r in rows) / n,
        "mrr": sum(r["rr"] for r in rows) / n,
        "precision_k": sum(r["prec"] for r in rows) / n,
        "p50_ms": statistics.median(ms),
        "p95_ms": ms[min(n - 1, int(0.95 * n))],
    }


def run_mode(mode: str, questions: list[dict], k: int, retrieve_fn) -> dict:
    retrieve_fn("warm up", k, mode)  # load models first so latency is fair
    rows = []
    for q in questions:
        start = time.perf_counter()
        results = retrieve_fn(q["q"], k, mode)
        ms = (time.perf_counter() - start) * 1000
        flags = [is_relevant(c, q) for c in results]
        first = flags.index(True) + 1 if True in flags else None
        rows.append({"hit1": bool(flags[:1] and flags[0]), "hit": any(flags),
                     "rr": 1 / first if first else 0.0, "prec": sum(flags) / k, "ms": ms})
    return compute_metrics(rows)


def run_answers(n: int, valid: list[dict], refusals: list[dict], retrieve_fn) -> dict:
    from app.llm import NO_ANSWER, answer
    sample = valid[::max(1, len(valid) // n)][:n]
    good = refused = 0
    for q in sample:
        res = answer(q["q"], 5, "rerank", retrieve_fn=retrieve_fn)
        cited_ok = any(is_relevant(res["sources"][i - 1], q) for i in res["cited"])
        good += bool(cited_ok and not res["invalid_citations"])
        time.sleep(6)  # stay under free-tier rate limits
    for q in refusals:
        res = answer(q["q"], 5, "rerank", retrieve_fn=retrieve_fn)
        refused += res["answer"].strip().startswith(NO_ANSWER[:12])
        time.sleep(6)
    return {"n": len(sample), "citation_accuracy": good / len(sample),
            "n_refusal": len(refusals), "refusal_rate": refused / max(1, len(refusals))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--pool", type=int, default=30)
    ap.add_argument("--answers", type=int, default=0)
    args = ap.parse_args()

    from app.retrieval import _load_chunks, retrieve
    chunks = _load_chunks()
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    refusals = [q for q in questions if q.get("refusal")]
    scored = [q for q in questions if not q.get("refusal")]
    valid = [q for q in scored if any(is_relevant(c, q) for c in chunks)]
    for q in scored:
        if q not in valid:
            print(f"Skipped (label not found in index): {q['q']}")

    retrieve_fn = lambda text, k, mode: retrieve(text, k, mode, pool=args.pool)  # noqa: E731
    k = args.k
    lines = [f"| Mode | Recall@1 | Recall@{k} | MRR | Precision@{k} | p50 latency | p95 latency |",
             "|---|---|---|---|---|---|---|"]
    for mode in MODES:
        print(f"Evaluating {mode}...")
        m = run_mode(mode, valid, k, retrieve_fn)
        lines.append(f"| {mode} | {m['recall_1']:.0%} | {m['recall_k']:.0%} | {m['mrr']:.2f} | "
                     f"{m['precision_k']:.0%} | {m['p50_ms']:.0f} ms | {m['p95_ms']:.0f} ms |")
    out = [f"# Evaluation results ({date.today()})", "",
           f"{len(valid)} labelled questions on the indexed repo, k={k}, rerank pool={args.pool}. "
           "Latency is retrieval only (no LLM), on a laptop CPU.", ""] + lines
    if args.answers:
        print("Testing LLM answers (slow)...")
        a = run_answers(args.answers, valid, refusals, retrieve_fn)
        out += ["", f"**Answers** ({a['n']} questions): citation accuracy {a['citation_accuracy']:.0%} "
                f"(cited a correct source, no invalid citations); refused {a['refusal_rate']:.0%} of "
                f"{a['n_refusal']} out-of-scope questions."]
    text = "\n".join(out)
    (HERE / "results.md").write_text(text + "\n", encoding="utf-8")
    print("\n" + text + "\n\nSaved to eval/results.md")
    from app import indexing
    indexing.close_client()


if __name__ == "__main__":
    main()
