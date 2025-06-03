from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

import coverage

from skippy_cov.config_handler import get_config

DEFAULT_GLOB_PATTERN = "test_*.py"


class FilterCandidatesError(ValueError):
    def __init__(self, *args, paths: list[Path], **kwargs):
        super().__init__(*args, **kwargs)
        self.message = f"Attempting to relativize based in multiple paths: {paths}"


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


def _fix_test_name(test_name: str) -> tuple[str, str]:
    """
    Removes everything after the last `|` from the test name and the first `::`
    In a file like `file.py::test_name|phase_name` the `|` separates the phase name
        and the first `::` separates the test name from the file_name
    This is because the context in coverage is always a string like `file_name.py::test_name`
        or `file_name.py::class_name::test_name`

    >>> _fix_test_name("file.py::test_name|phase_name")
    ('file.py', 'test_name')
    >>> _fix_test_name("file.py::class_name::test_name")
    ('file.py', 'class_name::test_name')
    """
    rhs, lhs = test_name.rsplit("|", 1)[0].split("::", 1)
    return (rhs, lhs)


def filter_by_path(
    candidates: list[FileTestCandidate],
    from_folders: list[Path],
    keep_prefix: bool = True,
) -> list[FileTestCandidate]:
    """
    Filters a list of FileTestCandidate objects based on a starting folder and depth.

    Args:
        candidates: A list of FileTestCandidate objects to filter.
        from_folders: A list of Path objects representing the starting folder.
        keep_prefix: A boolean, if true, the origial path is kept, if false it's removed
    Returns:
        A new list of FileTestCandidate objects that satisfy the filtering criteria.
    Raises:
        FilterCandidatesError: If `keep_prefix` is false and there's more than 1 path to filter,
                    Which doesn't make sense.
    """
    filtered_candidates: list[FileTestCandidate] = []

    if not keep_prefix and len(from_folders) > 1:
        raise FilterCandidatesError(paths=from_folders)

    for candidate in candidates:
        for filepath in from_folders:
            try:
                relative_path = candidate.path.relative_to(filepath)
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

    def get_tests(self, filepath: Path) -> list[FileTestCandidate]:
        found_tests: defaultdict[Path, set[str]] = defaultdict(set)
        for line_tests in self.db.contexts_by_lineno(filepath.as_posix()).values():
            for test in line_tests:
                if test:
                    src, test = _fix_test_name(test)
                    found_tests[Path(src)].add(test)
        return [
            FileTestCandidate(path=filepath, tests=tests)
            for (filepath, tests) in found_tests.items()
        ]
