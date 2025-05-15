from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from skippy_cov import select_tests_to_run
from skippy_cov.diff_handler import DiffHandler
from skippy_cov.utils import CoverageMap, filter_by_path

logger = logging.getLogger(__name__)


def run(
    diff_file: Path,
    coverage_file: Path,
    relative_to: list[Path] | None,
    keep_prefix: bool,
    display: bool = False,
) -> set[str]:
    """
    Run the test filter. If `display` = True will also print the output to stdout
    """
    diff_handler = DiffHandler(diff_file.read_text())
    coverage_map = CoverageMap(coverage_file)
    selected_tests = select_tests_to_run(diff_handler, coverage_map)
    tests = sorted(selected_tests)
    if not tests:
        logger.info("No specific tests selected to run based on changes and coverage.")
    if keep_prefix and relative_to and len(relative_to) > 1:
        logger.warning(
            "Trying to remove prefix with more than one path as filter is not allowed. "
            "The keep_prefix flag will be set to True"
        )
        keep_prefix = True

    if relative_to:
        selected_tests = filter_by_path(selected_tests, relative_to, keep_prefix)

    output = set()
    for test in selected_tests:
        output |= test.as_set()

    output_content = " ".join(output)
    if display:
        print(output_content)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Select pytest tests based on diff and coverage."
    )
    parser.add_argument(
        "--diff-file",
        required=False,
        help="Path to a file containing the git diff.",
        type=Path,
        default=Path("changes.diff"),
    )
    parser.add_argument(
        "--coverage-map-file",
        required=False,
        help="Path to the coverage map file (.coverage sqlite database).",
        type=Path,
        default=Path(".coverage"),
    )
    parser.add_argument(
        "--relative-to",
        required=False,
        help="Display only tests contained in a folder",
        type=Path,
        nargs="+",
        default=None,
    )
    parser.add_argument(
        "--keep-prefix",
        required=False,
        default=True,
        action="store_true",
        help="When using --relative-to, determine if the original path should be kept or removed",
    )
    parser.add_argument(
        "--strip-prefix",
        dest="keep_prefix",
        action="store_false",
        help="When using --relative-to, determine if the original path should be kept or removed",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging.", default=False
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if not args.diff_file.exists():
        print(
            f"skippy-cov: missing file `{args.diff_file.as_posix()}`. Unable to continue",
            file=sys.stderr,
        )
        sys.exit(1)

    run(
        args.diff_file,
        args.coverage_map_file,
        args.relative_to,
        args.keep_prefix,
        display=True,
    )
