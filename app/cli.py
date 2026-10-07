"""Command line tool.

  python -m app.cli index https://github.com/pallets/flask
  python -m app.cli search "how does routing work?"
  python -m app.cli search "dispatch_request" --mode bm25
  python -m app.cli update https://github.com/pallets/flask
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
    for f in iter_source_files(repo, include_noise=args.include_tests):
        chunks.extend(chunk_source_file(f))
    print("Reading commit history...")
    chunks.extend(chunk_commit(c) for c in get_commits(repo, args.max_commits))
    print(f"Total chunks: {len(chunks)}. Creating embeddings...")
    build_index(chunks, repo_name=repo.name)
    print('Done! Now try: python -m app.cli ask "your question"')


def cmd_update(args) -> None:
    """Re-index only what changed since the index was built."""
    from app.indexing import delete_paths, dump_chunks, upsert_chunks
    from app.update import indexed_files, plan_update
    start = time.perf_counter()
    try:
        indexed = dump_chunks()
    except Exception:
        print("No index found. Run first: python -m app.cli index <repo-url>")
        sys.exit(1)
    files_idx, commits_idx = indexed_files(indexed)
    print("Checking the repo for changes...")
    repo = clone_repo(args.url, pull=not args.no_pull)
    current = {f.path: f for f in iter_source_files(repo)}
    plan = plan_update(files_idx, {p: f.commit for p, f in current.items()})
    new_commits = [c for c in get_commits(repo, args.max_commits) if c.sha not in commits_idx]
    todo = plan["new"] + plan["changed"]
    print(f"New files: {len(plan['new'])}, changed: {len(plan['changed'])}, "
          f"removed: {len(plan['removed'])}, new commits: {len(new_commits)}")
    if not (todo or plan["removed"] or new_commits):
        print("Index is already up to date.")
        return
    new_chunks = [ch for p in todo for ch in chunk_source_file(current[p])]
    new_chunks += [chunk_commit(c) for c in new_commits]
    delete_paths(plan["removed"] + plan["changed"])
    upsert_chunks(new_chunks, repo.name)
    dump_chunks()
    print(f"Updated in {time.perf_counter() - start:.1f}s: re-embedded {len(new_chunks)} chunks "
          f"(a full re-index re-embeds all of them). Restart the web server to reload the index.")


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
    a.add_argument("--include-tests", action="store_true", help="also index tests/ and examples/")
    a.set_defaults(func=cmd_index)
    u = sub.add_parser("update")
    u.add_argument("url")
    u.add_argument("--max-commits", type=int, default=300)
    u.add_argument("--no-pull", action="store_true", help="compare with the local clone without git pull")
    u.set_defaults(func=cmd_update)
    modes = ["vector", "bm25", "hybrid", "rerank"]
    b = sub.add_parser("search")
    b.add_argument("question")
    b.add_argument("-k", type=int, default=5)
    b.add_argument("--mode", choices=modes, default="vector")
    b.set_defaults(func=cmd_search)
    c = sub.add_parser("ask")
    c.add_argument("question")
    c.add_argument("-k", type=int, default=5)
    c.add_argument("--mode", choices=modes, default="vector")
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
