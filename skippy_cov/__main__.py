from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from skippy_cov import select_tests_to_run, __version__
from skippy_cov.diff_handler import DiffHandler
from skippy_cov.utils import CoverageMap, filter_by_path

logger = logging.getLogger(__name__)


def run(
    diff: str,
    coverage_file: Path,
    relative_to: list[Path] | None,
    keep_prefix: bool,
    display: bool = False,
) -> set[str]:
    """
    Run the test filter. If `display` = True will also print the output to stdout
    """
    diff_handler = DiffHandler(diff)
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


def get_default_branch() -> str:
    """
    Determine the default branch to diff against.

    This function attempts to determine the default branch by inspecting the
    output of `git remote show origin`. If it fails to determine the branch
    (e.g., not in a git repository, or `origin` is not configured), it falls
    back to "main".

    Returns:
        str: The name of the default branch (e.g., "main", "develop").
    """
    try:
        output = subprocess.check_output(
            ["git", "remote", "show", "origin"], stderr=subprocess.DEVNULL, text=True
        )
        for line in output.splitlines():
            if "HEAD branch" in line:
                return line.split(":")[-1].strip()
    except Exception:
        logger.info("Could not determine default branch, falling back to 'main'.")
    return "main"


def get_diff_content(diff_arg):
    """
    Get the diff content based on the provided argument.
    It can either be a file path or a git ref/branch to diff against.
    """
    # If it's a file path and exists, read it as a file
    if diff_arg:  # Only try Path if diff_arg is not None/empty
        path = Path(diff_arg)
        if path.exists():
            return path.read_text()
    # Otherwise, treat as git diff argument (branch/refspec)
    branch = diff_arg if diff_arg else get_default_branch()
    try:
        diff = subprocess.check_output(
            ["git", "diff", branch], stderr=subprocess.DEVNULL, text=True
        )
    except Exception as e:
        print(f"skippy-cov: failed to get git diff for '{branch}': {e}", file=sys.stderr)
        sys.exit(1)
    else:
        return diff

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Select pytest tests based on diff and coverage."
    )
    parser.add_argument(
        "--diff",
        required=False,
        help="Path to a diff file or a git ref/branch to diff against (default: main branch).",
        default=None,
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
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args(argv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    diff_content = (
        get_diff_content(args.diff) if args.diff is not None else get_diff_content(None)
    )

    run(
        diff_content,
        args.coverage_map_file,
        args.relative_to,
        args.keep_prefix,
        display=True,
    )
