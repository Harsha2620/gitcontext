"""Command line tool.

  python -m app.cli index https://github.com/pallets/flask
  python -m app.cli search "how does routing work?"
  python -m app.cli search "dispatch_request" --mode bm25
"""
import argparse
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
    print('Done! Now try: python -m app.cli search "your question"')


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


def main() -> None:
    p = argparse.ArgumentParser(prog="gitcontext")
    sub = p.add_subparsers(required=True)
    a = sub.add_parser("index")
    a.add_argument("url")
    a.add_argument("--max-commits", type=int, default=300)
    a.set_defaults(func=cmd_index)
    b = sub.add_parser("search")
    b.add_argument("question")
    b.add_argument("-k", type=int, default=5)
    b.add_argument("--mode", choices=["vector", "bm25", "hybrid", "rerank"], default="rerank")
    b.set_defaults(func=cmd_search)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
