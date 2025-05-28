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
        "--skippy-cov-diff",
        required=False,
        help="Path to a diff file or a git ref/branch to diff against (default: main branch).",
        default=None,
    )
    group.addoption(
        "--skippy-cov-coverage-file",
        required=False,
        help="Path to the coverage file (.coverage sqlite database).",
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
    diff_arg = config.getoption("skippy_cov_diff")
    cov_file = config.getoption("skippy_cov_coverage_file")
    keep_prefix = config.getoption("skippy_cov_keep_prefix")
    if not skippy_cov:
        return

    # Import get_diff_content from __main__ to match CLI logic
    from skippy_cov.__main__ import get_diff_content

    diff_content = (
        get_diff_content(diff_arg) if diff_arg is not None else get_diff_content(None)
    )

    relative_to = [Path(x) for x in config.args if x]
    selected_tests = run(
        diff_content,
        cov_file,
        relative_to,
        keep_prefix,
    )
    if selected_tests:
        config.args = selected_tests
    else:
        pytest.exit("skippy-cov: couldn't find any tests to filter.", returncode=5)
