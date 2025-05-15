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
        default=Path("changes.diff"),
    )
    group.addoption(
        "--skippy-cov-coverage-map-file",
        required=False,
        help="Path to the coverage map file (.coverage sqlite database).",
        type=Path,
        default=Path(".coverage"),
    )
    group.addoption(
        "--skippy-cov-keep-prefix",
        required=False,
        default=True,
        dest="skippy_cov_keep_prefix",
        action="store_true",
        help="When using --skippy-cov-relative-to, determine if the original path should be kept or removed",
    )
    group.addoption(
        "--skippy-cov-strip-prefix",
        dest="skippy_cov_keep_prefix",
        action="store_false",
        help="When using --skippy-cov-relative-to, determine if the original path should be kept or removed",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Attempts to filter tests using skippy-cov
    """
    skippy_cov = config.getoption("skippy_cov")
    diff_file = config.getoption("skippy_cov_diff_file")
    cov_map_file = config.getoption("skippy_cov_coverage_map_file")
    keep_prefix = config.getoption("skippy_cov_keep_prefix")
    if not skippy_cov:
        return
    if not diff_file.exists():
        pytest.exit(
            f"skippy-cov: missing file `{diff_file.as_posix()}`. Unable to continue",
            returncode=1,
        )
    relative_to = [Path(x) for x in config.args if x]
    selected_tests = run(diff_file, cov_map_file, relative_to, keep_prefix)
    if selected_tests:
        config.args = selected_tests
    else:
        pytest.exit("skippy-cov: couldn't find any tests to filter.", returncode=5)
