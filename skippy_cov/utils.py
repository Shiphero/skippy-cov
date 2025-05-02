from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

import coverage

from skippy_cov.config_handler import get_config

DEFAULT_GLOB_PATTERN = "test_*.py"


@dataclass
class FileTestCandidate:
    path: Path
    tests: set[str]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, FileTestCandidate):
            raise NotImplementedError
        return self.path < other.path

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileTestCandidate):
            raise NotImplementedError
        return self.path == other.path and self.tests == other.tests

    def as_set(self) -> set[str]:
        tests = set()
        for test in self.tests:
            tests.add(f"{self.path.as_posix()}::{test}")
        return tests


def is_test_file(file_path: Path) -> bool:
    """
    Checks if a file is a test file based on its name.

    Checks if a config file is present. If so, tries to use the `python_files` key
    from the config file.
    Otherwise uses the default glob pattern. (test_*.py)
    """

    # TODO: consider pytest flags such as `ignore`, `addopts`, etc...
    # config_handler.ConfigHandler should already handle it,
    #   but I want to have something working before sinking more hours into this
    # SEE: https://docs.pytest.org/en/stable/example/pythoncollection.html#changing-naming-conventions
    cfg = get_config()
    if (
        bool(cfg)
        and (patterns := cfg.get_value("python_files"))
        and isinstance(patterns, str)
    ):
        return any(fnmatch(file_path.name, pattern) for pattern in patterns.split(" "))

    return fnmatch(file_path.name, DEFAULT_GLOB_PATTERN)


def _fix_test_name(test_name: str) -> str:
    """
    Removes everything after the last `|` from the test name.
    Most likely, this is the phase name and not part of the test name or parameters.
    """
    return test_name.rsplit("|", 1)[0]


def filter_by_path(
    candidates: list[FileTestCandidate], from_folder: Path, keep_prefix: bool = True
) -> list[FileTestCandidate]:
    """
    Filters a list of FileTestCandidate objects based on a starting folder and depth.

    Args:
        candidates: A list of FileTestCandidate objects to filter.
        from_folder: A Path object representing the starting folder.
        keep_prefix: A boolean, if true, the origial path is kept, if false it's removed
    Returns:
        A new list of FileTestCandidate objects that satisfy the filtering criteria.
    """
    filtered_candidates: list[FileTestCandidate] = []

    for candidate in candidates:
        try:
            relative_path = candidate.path.relative_to(from_folder)
        except ValueError:
            # The candidate is not within the from_folder, so skip it
            continue
        if not keep_prefix:
            candidate.path = relative_path
        filtered_candidates.append(candidate)

    return filtered_candidates


class CoverageMap:
    db: coverage.CoverageData

    def __init__(self, filepath: Path):
        self.db = coverage.CoverageData(filepath.name)
        self.db.read()

    def get_tests(self, filepath: Path) -> FileTestCandidate | None:
        tests = set()
        for line_tests in self.db.contexts_by_lineno(filepath.name).values():
            tests |= {_fix_test_name(test) for test in line_tests}
        if tests:
            return FileTestCandidate(path=filepath, tests=tests)
        return None
