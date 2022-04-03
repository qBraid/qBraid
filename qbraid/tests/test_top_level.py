"""Test top-level qbraid functionality"""


def test_about():
    try:
        from qbraid import about

        about()
    except Exception:
        assert False
    assert True


def test_version():
    try:
        from qbraid import __version__
    except Exception:
        assert False
    assert True
