from __future__ import annotations

from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path

import coverage

from skippy_cov.config_handler import get_config

DEFAULT_GLOB_PATTERN = "test_*.py"


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
    cfg = get_config(Path.cwd())
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


def load_coverage_map(filepath: Path) -> defaultdict[Path, set[str]]:
    """
    Load coverage data from a coverage database file.
    Maps file paths to sets of test names. (skipping phase names)
    """
    db = coverage.CoverageData(filepath)
    db.read()
    files = db._file_map.keys()
    coverage_map: defaultdict[Path, set[str]] = defaultdict(set)

    for file in files:
        tests = db.contexts_by_lineno(file)
        for line_tests in tests.values():
            coverage_map[Path(file)] = coverage_map[Path(file)].union([
                _fix_test_name(test) for test in line_tests
            ])

    return coverage_map
