"""Phase 9: decide what to re-index. Pure functions (no heavy imports) so they are easy to test."""


def indexed_files(chunks: list[dict]) -> tuple[dict[str, str], set[str]]:
    """From stored chunks: {file path: last-commit hash it was indexed at}, and the set of indexed commit hashes."""
    files: dict[str, str] = {}
    commits: set[str] = set()
    for c in chunks:
        if c.get("kind") == "commit":
            commits.add(c["commit"])
        else:
            files[c["path"]] = c["commit"]
    return files, commits


def plan_update(indexed: dict[str, str], current: dict[str, str]) -> dict[str, list[str]]:
    """Compare {path: commit} in the index with {path: commit} in the repo right now."""
    return {
        "removed": sorted(indexed.keys() - current.keys()),
        "new": sorted(current.keys() - indexed.keys()),
        "changed": sorted(p for p in current.keys() & indexed.keys() if current[p] != indexed[p]),
    }
