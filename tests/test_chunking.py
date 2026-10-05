from app.chunking import chunk_markdown, chunk_python
from app.ingestion import SourceFile

PY = '''
import os

def hello(name):
    return "hi " + name

class Greeter:
    def run(self):
        return hello("x")
'''


def _file(text, path="a.py", kind="code"):
    return SourceFile(path, text, kind, "2026-01-01", "dev", "abc123")


def test_python_chunks_by_function_and_class():
    names = [c.metadata["name"] for c in chunk_python(_file(PY))]
    assert names == ["hello", "Greeter"]


def test_syntax_error_falls_back_to_lines():
    assert len(chunk_python(_file("def broken(:\n  pass\n"))) >= 1


def test_markdown_splits_on_headings():
    md = "# Title\nintro\n\n## Usage\nrun it\n"
    chunks = chunk_markdown(_file(md, "README.md", "doc"))
    assert [c.metadata["name"] for c in chunks] == ["Title", "Usage"]


def test_metadata_attached():
    meta = chunk_python(_file(PY))[0].metadata
    assert meta["path"] == "a.py" and meta["author"] == "dev"
