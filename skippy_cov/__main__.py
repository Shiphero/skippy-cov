from __future__ import annotations

import argparse
import logging
from pathlib import Path

from skippy_cov import select_tests_to_run
from skippy_cov.diff_handler import DiffHandler
from skippy_cov.utils import CoverageMap

logger = logging.getLogger(__name__)


def run(diff_file: Path, coverage_file: Path) -> str:
    diff_handler = DiffHandler(diff_file.read_text())
    coverage_map = CoverageMap(coverage_file)
    selected_tests = select_tests_to_run(diff_handler, coverage_map)
    tests = sorted(selected_tests)
    if not tests:
        logger.info("No specific tests selected to run based on changes and coverage.")

    output_content = " ".join(set(tests))
    print(output_content)
    return output_content


def main():
    parser = argparse.ArgumentParser(
        description="Select pytest tests based on diff and coverage."
    )
    parser.add_argument(
        "--diff-file",
        required=True,
        help="Path to a file containing the list of changed files (one per line).",
        type=Path,
    )
    parser.add_argument(
        "--coverage-map-file",
        required=True,
        help="Path to the coverage map file (JSON format expected).",
        type=Path,
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging.", default=False
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    run(args.diff_file, args.coverage_map_file)
