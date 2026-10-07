from app.update import indexed_files, plan_update


def test_indexed_files_separates_files_and_commits():
    chunks = [{"kind": "function", "path": "a.py", "commit": "c1"},
              {"kind": "doc", "path": "README.md", "commit": "c2"},
              {"kind": "commit", "path": "commit:abc", "commit": "abc"}]
    files, commits = indexed_files(chunks)
    assert files == {"a.py": "c1", "README.md": "c2"} and commits == {"abc"}


def test_plan_finds_new_changed_and_removed_files():
    plan = plan_update({"a.py": "1", "b.py": "1", "old.py": "1"},
                       {"a.py": "1", "b.py": "2", "fresh.py": "3"})
    assert plan == {"removed": ["old.py"], "new": ["fresh.py"], "changed": ["b.py"]}


def test_plan_is_empty_when_nothing_changed():
    plan = plan_update({"a.py": "1"}, {"a.py": "1"})
    assert plan == {"removed": [], "new": [], "changed": []}
