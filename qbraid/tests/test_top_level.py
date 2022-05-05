"""
Unit tests for qbraid top-level functionality

"""

import sys
from unittest.mock import Mock

import pytest

from qbraid._about import about
from qbraid.ipython_utils import running_in_jupyter
from qbraid.exceptions import PackageValueError

# pylint: disable=missing-function-docstring,redefined-outer-name


def test_about():
    about()
    assert True


def test_package_value_error():
    with pytest.raises(PackageValueError):
        raise PackageValueError("custom msg")


def test_running_in_jupyter():
    assert not running_in_jupyter()


def test_ipython_imported_but_ipython_none():
    _mock_ipython(None)
    assert not running_in_jupyter()


def test_ipython_imported_but_not_in_jupyter():
    _mock_ipython(MockIPython(None))
    assert not running_in_jupyter()


def test_ipython_imported_and_in_jupyter():
    _mock_ipython(MockIPython("non empty kernel"))
    assert running_in_jupyter()


def get_ipython():
    pass


def _mock_ipython(get_ipython_result):
    module = sys.modules["test_top_level"]
    sys.modules["IPython"] = module

    get_ipython = Mock(return_value=get_ipython_result)
    sys.modules["IPython"].__dict__["get_ipython"] = get_ipython


class MockIPython:
    """Mock IPython class for testing"""

    def __init__(self, kernel):
        self.kernel = kernel
