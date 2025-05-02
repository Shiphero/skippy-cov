from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

import coverage

from skippy_cov.config_handler import get_config

DEFAULT_GLOB_PATTERN = "test_*.py"


@dataclass
class TestCandidate:
    path: Path
    tests: set[str]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, TestCandidate):
            raise NotImplementedError
        return self.path < other.path

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TestCandidate):
            raise NotImplementedError
        return self.path == other.path and self.tests == other.tests


def is_test_file(file_path: Path) -> bool:
    """
    Checks if a file is a test file based on its name.

    Checks if a config file is present. If so, tries to use the `python_files` key
    from the config file.
    Otherwise uses the default glob pattern. (test_*.py)
    """

    # TODO: consider pytest flags such as `ignore`, `addopts`, etc...
    # config_handler.ConfigHandler should already handle it,
    #   but I want to have something working before sincking more hours into this
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


class CoverageMap:
    db: coverage.CoverageData

    def __init__(self, filepath: Path):
        self.db = coverage.CoverageData(filepath.name)
        self.db.read()

    def get_tests(self, filepath: Path) -> TestCandidate | None:
        tests = set()
        for line_tests in self.db.contexts_by_lineno(filepath.name).values():
            tests |= {_fix_test_name(test) for test in line_tests}
        if tests:
            return TestCandidate(path=filepath, tests=tests)
        return None
