from pathlib import Path

import pytest
from pytest_mock import MockFixture

from skippy_cov.utils import _fix_test_name, is_test_file


@pytest.mark.parametrize(
    "fname,expected", [("test_file.py", True), ("testfile.py", False)]
)
def test_noconfig_is_test_file(fname: str, expected: bool, mocker: MockFixture) -> None:
    mocker.patch("skippy_cov.utils.get_config", return_value=None)
    assert is_test_file(Path(fname)) == expected


def test_config_is_test_file(mocker: MockFixture) -> None:
    config_mock = mocker.MagicMock()
    config_mock.get_value.return_value = "check_*.py"
    mocker.patch("skippy_cov.utils.get_config", return_value=config_mock)
    assert is_test_file(Path("check_file.py"))
    assert not is_test_file(Path("test_file.py"))


@pytest.mark.parametrize(
    "name,expected",
    [
        ("test_file.py::test_name", "test_file.py::test_name"),
        ("test_file.py::ClassName::test_name", "test_file.py::ClassName::test_name"),
        (
            "test_file.py::test_name[param1, param2]",
            "test_file.py::test_name[param1, param2]",
        ),
        (
            "test_file.py::test_name[param1, param2]|phase",
            "test_file.py::test_name[param1, param2]",
        ),
        (
            "test_file.py::test_name[param|param]|phase",
            "test_file.py::test_name[param|param]",
        ),
    ],
)
def test_fix_test_name(name: str, expected: str) -> None:
    assert _fix_test_name(name) == expected
