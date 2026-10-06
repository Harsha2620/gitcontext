"""Command line tool.

  python -m app.cli index https://github.com/pallets/flask
  python -m app.cli search "how does routing work?"
  python -m app.cli search "dispatch_request" --mode bm25
  python -m app.cli ask "How does Flask match a URL to a view function?"
"""
import argparse
import sys
import time

from app.chunking import chunk_commit, chunk_source_file
from app.ingestion import clone_repo, get_commits, iter_source_files


def cmd_index(args) -> None:
    from app.indexing import build_index
    print("Cloning repo...")
    repo = clone_repo(args.url)
    chunks = []
    print("Reading and chunking files...")
    for f in iter_source_files(repo):
        chunks.extend(chunk_source_file(f))
    print("Reading commit history...")
    chunks.extend(chunk_commit(c) for c in get_commits(repo, args.max_commits))
    print(f"Total chunks: {len(chunks)}. Creating embeddings...")
    build_index(chunks, repo_name=repo.name)
    print('Done! Now try: python -m app.cli ask "your question"')


def cmd_search(args) -> None:
    from app.retrieval import retrieve
    start = time.perf_counter()
    results = retrieve(args.question, args.k, args.mode)
    ms = (time.perf_counter() - start) * 1000
    print(f"mode={args.mode}  latency={ms:.0f} ms")
    for i, r in enumerate(results, 1):
        snippet = r["text"][:300].replace("\n", "\n    ")
        print(f"\n#{i}  score={r['score']:.3f}  {r['kind']}  {r['path']} ({r['name']})")
        print(f"    by {r['author']} on {r['last_modified'][:10]}\n    {snippet}")


def cmd_ask(args) -> None:
    from app.llm import answer, source_label
    try:
        res = answer(args.question, args.k, args.mode)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:  # network, bad key, rate limit...
        print(f"LLM request failed: {e}")
        sys.exit(1)

    print("\n" + res["answer"] + "\n")
    print("Sources:")
    for i, c in enumerate(res["sources"], 1):
        mark = "*" if i in res["cited"] else " "
        print(f" {mark}[{i}] {source_label(c)}")
    if res["invalid_citations"]:
        print(f"Warning: answer cited unknown sources {res['invalid_citations']}")
    print(f"\n(* = cited in answer)  retrieval={res['retrieval_ms']:.0f} ms  total={res['total_ms']:.0f} ms")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # avoid Windows unicode crashes
    p = argparse.ArgumentParser(prog="gitcontext")
    sub = p.add_subparsers(required=True)
    a = sub.add_parser("index")
    a.add_argument("url")
    a.add_argument("--max-commits", type=int, default=300)
    a.set_defaults(func=cmd_index)
    modes = ["vector", "bm25", "hybrid", "rerank"]
    b = sub.add_parser("search")
    b.add_argument("question")
    b.add_argument("-k", type=int, default=5)
    b.add_argument("--mode", choices=modes, default="rerank")
    b.set_defaults(func=cmd_search)
    c = sub.add_parser("ask")
    c.add_argument("question")
    c.add_argument("-k", type=int, default=5)
    c.add_argument("--mode", choices=modes, default="rerank")
    c.set_defaults(func=cmd_ask)
    args = p.parse_args()
    try:
        args.func(args)
    finally:
        idx = sys.modules.get("app.indexing")
        if idx:
            idx.close_client()


if __name__ == "__main__":
    main()
