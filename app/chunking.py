"""Phase 3: split files into smart chunks (by function/class, not random size)."""
import ast
from dataclasses import dataclass, field

from app.ingestion import Commit, SourceFile

MAX_CHARS = 4000


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def _make(f: SourceFile, name: str, body: str, start: int, end: int, kind: str) -> Chunk:
    text = f"File: {f.path}\n{kind}: {name}\n\n{body}"
    meta = {
        "path": f.path, "name": name, "kind": kind,
        "start_line": start, "end_line": end,
        "last_modified": f.last_modified, "author": f.author, "commit": f.commit,
    }
    return Chunk(text, meta)


def chunk_lines(f: SourceFile, size: int = 60, overlap: int = 10) -> list[Chunk]:
    """Fallback: sliding window of lines."""
    lines = f.text.splitlines()
    out, i = [], 0
    while i < len(lines):
        part = lines[i:i + size]
        if "".join(part).strip():
            out.append(_make(f, f"lines {i + 1}-{i + len(part)}", "\n".join(part),
                             i + 1, i + len(part), "block"))
        i += size - overlap
    return out


def chunk_python(f: SourceFile) -> list[Chunk]:
    try:
        tree = ast.parse(f.text)
    except SyntaxError:
        return chunk_lines(f)
    lines = f.text.splitlines()
    out: list[Chunk] = []

    def add(name: str, node, kind: str) -> None:
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        body = "\n".join(lines[start - 1:node.end_lineno])
        out.append(_make(f, name, body, start, node.end_lineno, kind))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add(node.name, node, "function")
        elif isinstance(node, ast.ClassDef):
            size = len("\n".join(lines[node.lineno - 1:node.end_lineno]))
            if size <= MAX_CHARS:
                add(node.name, node, "class")
            else:  # big class: one chunk per method
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        add(f"{node.name}.{child.name}", child, "method")
    return out or chunk_lines(f)


def chunk_markdown(f: SourceFile, max_chars: int = 1500) -> list[Chunk]:
    sections, current = [], []
    for line in f.text.splitlines():
        if line.startswith("#") and current:
            sections.append(current)
            current = []
        current.append(line)
    if current:
        sections.append(current)

    out = []
    for sec in sections:
        title = sec[0].lstrip("# ").strip() or "intro"
        body, pieces = "\n".join(sec), []
        while len(body) > max_chars:  # split long sections at a paragraph break
            cut = body.rfind("\n\n", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            pieces.append(body[:cut])
            body = body[cut:].lstrip()
        pieces.append(body)
        for piece in pieces:
            if piece.strip():
                out.append(_make(f, title, piece, 0, 0, "doc"))
    return out


def chunk_source_file(f: SourceFile) -> list[Chunk]:
    if f.kind == "code" and f.path.endswith(".py"):
        return chunk_python(f)
    return chunk_markdown(f)


def chunk_commit(c: Commit) -> Chunk:
    text = f"Commit {c.sha[:8]} by {c.author} on {c.date}\n{c.subject}\n{c.body}".strip()
    meta = {"path": f"commit:{c.sha[:8]}", "name": c.subject, "kind": "commit",
            "start_line": 0, "end_line": 0, "last_modified": c.date,
            "author": c.author, "commit": c.sha}
    return Chunk(text, meta)
