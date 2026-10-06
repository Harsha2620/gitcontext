from app.ingestion import is_noise


def test_noise_files_are_detected():
    assert is_noise("tests/test_basic.py")
    assert is_noise("examples/tutorial/flaskr/__init__.py")
    assert is_noise("src/pkg/tests/helpers.py")
    assert is_noise("docs/conf.py")


def test_real_sources_are_kept():
    assert not is_noise("src/flask/app.py")
    assert not is_noise("src/flask/testing.py")  # a file called testing.py is real code
    assert not is_noise("docs/config.rst")
