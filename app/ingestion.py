"""Phase 2: download a GitHub repo and read its files + commit history."""
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import REPOS_DIR

CODE_EXT = {".py"}
DOC_EXT = {".md", ".rst", ".txt"}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
MAX_FILE_BYTES = 200_000


@dataclass
class SourceFile:
    path: str
    text: str
    kind: str  # "code" or "doc"
    last_modified: str
    author: str
    commit: str


@dataclass
class Commit:
    sha: str
    author: str
    date: str
    subject: str
    body: str


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="ignore",
    )
    return result.stdout.strip()


def clone_repo(url: str) -> Path:
    """Clone the repo (or update it if we already have it)."""
    name = url.rstrip("/").removesuffix(".git").split("/")[-1]
    dest = REPOS_DIR / name
    if dest.exists():
        subprocess.run(["git", "-C", str(dest), "pull"], check=True)
    else:
        REPOS_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", url, str(dest)], check=True)
    return dest


def iter_source_files(repo: Path):
    """Yield every code/doc file with its last commit info."""
    for p in sorted(repo.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.parts):
            continue
        ext = p.suffix.lower()
        if ext not in CODE_EXT | DOC_EXT or p.stat().st_size > MAX_FILE_BYTES:
            continue
        rel = p.relative_to(repo).as_posix()
        info = _git(repo, "log", "-1", "--format=%H|%an|%aI", "--", rel)
        sha, author, date = (info.split("|") + ["", "", ""])[:3]
        text = p.read_text(encoding="utf-8", errors="ignore")
        yield SourceFile(rel, text, "code" if ext in CODE_EXT else "doc", date, author, sha)


def get_commits(repo: Path, limit: int = 300) -> list[Commit]:
    """Read the latest commits from git history."""
    raw = _git(repo, "log", f"-n{limit}", "--format=%H%x1f%an%x1f%aI%x1f%s%x1f%b%x1e")
    commits = []
    for entry in raw.split("\x1e"):
        parts = entry.strip().split("\x1f")
        if len(parts) == 5:
            commits.append(Commit(*parts))
    return commits
