import logging
from pathlib import Path

import pytest

from skippy_cov.__main__ import run

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    group = parser.getgroup("skippy-cov", "Options for skippy coverage-based collection")

    group.addoption(
        "--skippy-cov",
        required=False,
        dest="skippy_cov",
        action="store_true",
        help="Enable skippy-cov",
    )

    group.addoption(
        "--skippy-cov-diff-file",
        required=False,
        help="Path to a file containing the git diff.",
        type=Path,
    )
    group.addoption(
        "--skippy-cov-coverage-map-file",
        required=False,
        help="Path to the coverage map file (.coverage sqlite database).",
        type=Path,
    )
    group.addoption(
        "--skippy-cov-relative-to",
        required=False,
        help="Display only tests contained in a folder",
        type=Path,
        default=None,
    )
    group.addoption(
        "--skippy-cov-keep-prefix",
        required=False,
        dest="skippy_cov_keep_prefix",
        action="store_true",
        help="When using --relative-to, determine if the original path should be kept or removed",
    )
    group.addoption(
        "--skippy-cov-strip-prefix",
        dest="skippy_cov_keep_prefix",
        action="store_false",
        help="When using --relative-to, determine if the original path should be kept or removed",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    """
    Attempts to filter tests using skippy-cov
    """
    skippy_cov = config.getoption("skippy_cov")
    diff_file = config.getoption("skippy_cov_diff_file")
    cov_map_file = config.getoption("skippy_cov_coverage_map_file")
    if not skippy_cov:
        return
    if not diff_file or not cov_map_file:
        logging.warn(
            f"skippy-cov can't find all artifacts to run: {diff_file=}, {cov_map_file=}"
        )
        return

    relative_to = config.getoption("skippy_cov_relative_to")
    keep_prefix = config.getoption("skippy_cov_keep_prefix")
    selected_tests = run(diff_file, cov_map_file, relative_to, keep_prefix)
    if selected_tests:
        original = list(items)
        items.clear()
        wanted = set(original)
        for item in original:
            if item.nodeid in wanted:
                items.append(item)
        missing = wanted - {item.nodeid for item in items}
        if missing:
            logging.warn(f"skippy-cov: missing tests: {missing}")
    else:
        logging.warn(
            "skippy-cov: couldn't find any tests to filter running the full suite."
        )
