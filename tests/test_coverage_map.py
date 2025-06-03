from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from skippy_cov.utils import CoverageMap, FileTestCandidate


@pytest.fixture
def mocked_coverage(mocker: MockerFixture) -> MagicMock:
    mock = mocker.patch("skippy_cov.utils.coverage.CoverageData")
    coverage_db: MagicMock = mock.return_value
    coverage_db.read.return_value = True
    coverage_db._file_map.keys.return_value = ["source.py"]
    coverage_db.contexts_by_lineno.return_value = {
        1: ["test.py::test1|run", "test.py::test2|run"],
    }
    return coverage_db


def test_load_coverage_map(mocked_coverage: MagicMock) -> None:
    coverage_map = CoverageMap(Path("coverage.db"))
    assert coverage_map.get_tests(Path("source.py")) == [
        FileTestCandidate(
            path=Path("test.py"),
            tests={
                "test1",
                "test2",
            },
        )
    ]


def test_load_coverage_map_nested_folder(mocked_coverage: MagicMock) -> None:
    """
    Ensure the path is correctly parsed to the coverage db
    """
    coverage_map = CoverageMap(Path("coverage.db"))
    candidates = coverage_map.get_tests(Path("src/source.py"))
    mocked_coverage.contexts_by_lineno.assert_called_with("src/source.py")
    assert candidates and candidates[0].path == Path("test.py")
