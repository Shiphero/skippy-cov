from pathlib import Path

import pytest
from pytest_mock import MockFixture

from skippy_cov.utils import (
    FileTestCandidate,
    FilterCandidatesError,
    _fix_test_name,
    filter_by_path,
    is_test_file,
)


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
        ("test_file.py::test_name", ("test_file.py", "test_name")),
        ("test_file.py::ClassName::test_name", ("test_file.py", "ClassName::test_name")),
        (
            "test_file.py::test_name[param1, param2]",
            ("test_file.py", "test_name[param1, param2]"),
        ),
        (
            "test_file.py::test_name[param1, param2]|phase",
            ("test_file.py", "test_name[param1, param2]"),
        ),
        (
            "test_file.py::test_name[param|param]|phase",
            ("test_file.py", "test_name[param|param]"),
        ),
    ],
)
def test_fix_test_name(name: str, expected: str) -> None:
    assert _fix_test_name(name) == expected


def test_filter_paths():
    candidates = [
        FileTestCandidate(path=Path("/good/1"), tests=set()),
        FileTestCandidate(path=Path("/good/2"), tests=set()),
        FileTestCandidate(path=Path("/bad/1"), tests=set()),
        FileTestCandidate(path=Path("/bad/2"), tests=set()),
    ]
    expected = [
        FileTestCandidate(path=Path("1"), tests=set()),
        FileTestCandidate(path=Path("2"), tests=set()),
    ]
    assert filter_by_path(candidates, [Path("/good")], keep_prefix=False) == expected


def test_filter_paths_prefixed():
    candidates = [
        FileTestCandidate(path=Path("/good/1"), tests=set()),
        FileTestCandidate(path=Path("/good/2"), tests=set()),
        FileTestCandidate(path=Path("/bad/1"), tests=set()),
        FileTestCandidate(path=Path("/bad/2"), tests=set()),
    ]
    expected = [
        FileTestCandidate(path=Path("/good/1"), tests=set()),
        FileTestCandidate(path=Path("/good/2"), tests=set()),
    ]
    assert filter_by_path(candidates, [Path("/good")], keep_prefix=True) == expected


def test_filter_paths_prefixed_multiple_paths():
    candidates = [
        FileTestCandidate(path=Path("/good/1"), tests=set()),
        FileTestCandidate(path=Path("/good/2"), tests=set()),
        FileTestCandidate(path=Path("/better/1"), tests=set()),
        FileTestCandidate(path=Path("/better/2"), tests=set()),
        FileTestCandidate(path=Path("/bad/1"), tests=set()),
        FileTestCandidate(path=Path("/bad/2"), tests=set()),
    ]
    expected = [
        FileTestCandidate(path=Path("/good/1"), tests=set()),
        FileTestCandidate(path=Path("/good/2"), tests=set()),
        FileTestCandidate(path=Path("/better/1"), tests=set()),
        FileTestCandidate(path=Path("/better/2"), tests=set()),
    ]
    assert (
        filter_by_path(candidates, [Path("/good"), Path("/better")], keep_prefix=True)
        == expected
    )


def test_filter_paths_no_prefix_multiple_paths():
    with pytest.raises(FilterCandidatesError):
        filter_by_path([], [Path("/1"), Path("/2")], keep_prefix=False)


def test_generate_set():
    candidate = FileTestCandidate(path=Path("tests.py"), tests={"test1", "test2"})
    assert candidate.as_set() == {"tests.py::test1", "tests.py::test2"}
