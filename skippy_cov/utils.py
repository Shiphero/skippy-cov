from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import coverage


def is_test_file(file_path: Path) -> bool:
    return True


def _fix_test_name(test_name: str) -> str:
    return test_name.split("|")[0]


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
