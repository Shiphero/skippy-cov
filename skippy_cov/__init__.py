from __future__ import annotations

import ast
import logging
from pathlib import Path

from skippy_cov.diff_handler import DiffHandler
from skippy_cov.tests_finder import ASTTestsFinder
from skippy_cov.utils import CoverageMap, is_test_file

logger = logging.getLogger(__name__)


def discover_tests_in_file(file_path: Path) -> list[str]:
    """
    Discovers tests within a given Python file using AST parsing.
    Finds top-level functions (sync/async) starting with 'test_' and
    methods (sync/async) starting with 'test_' within classes
    starting with 'Test'.

    Args:
        file_path: The path to the Python file.

    Returns:
        A list of test identifiers in pytest format 'file::[Class::]test_name'.
        Returns an empty list if the file is not a test file, doesn't exist,
        cannot be read, or contains syntax errors preventing AST parsing.
    """
    logger.debug(f"Discovering tests in {file_path} using AST...")
    if not is_test_file(file_path):
        logger.debug(
            f"Skipping AST discovery: File path '{file_path}' "
            "doesn't match test file pattern."
        )
        return []
    if not file_path.exists() or not file_path.is_file():
        logger.debug(
            f"Skipping AST discovery: File path '{file_path}' "
            "does not exist or is not a file."
        )
        return []

    try:
        tree = ast.parse(file_path.read_text(), filename=file_path.name)

    except Exception as e:
        logger.warning(
            f"Could not discover tests via AST in '{file_path}' "
            f"due to unexpected error: {e}"
        )
        return []

    try:
        finder = ASTTestsFinder(file_path)
        finder.visit(tree)
        found_tests = finder.tests

        if found_tests:
            logger.debug(
                f"Found {len(found_tests)} test(s) in '{file_path}' "
                f"via AST: {found_tests}"
            )
        else:
            logger.debug(f"No tests found matching in '{file_path}' via AST.")

    except Exception as e:
        logger.warning(f"Error during AST traversal of '{file_path}': {e}")
        return []

    else:
        return found_tests


def select_tests_to_run(
    diff_handler: DiffHandler,
    coverage_map: CoverageMap,
) -> set[str]:
    """
    Determines the set of tests to run based on changed files and coverage.
    """
    tests_to_run: set[str] = set()
    run_all_tests_flag = False

    logger.debug(f"Processing {len(diff_handler.changed_files)} changed file(s)...")
    logger.debug(f"Changed files: {diff_handler.changed_files}")

    for file_path in diff_handler.changed_files:
        # 1. If the changed file is a source file with known coverage
        if tests_for_file := coverage_map.get_tests(file_path):
            logger.debug(
                f"Source file '{file_path}' changed. Adding {len(tests_for_file)}"
                "related test(s) from coverage map.",
            )
            tests_to_run.update(tests_for_file)

        # 2. If the changed file is a test file itself
        # Use the discovery function, which internally checks if it's a test file
        # This handles added/modified test files.
        # If a test file is changed, all tests in it will be run
        tests_in_file = discover_tests_in_file(file_path)
        if tests_in_file:
            logger.debug(
                f"Test file '{file_path}' changed or contains tests."
                f" Adding all {len(tests_in_file)} tests from this file.",
            )
            tests_to_run.update(tests_in_file)

        # 3. Handle files not in coverage map and not identified as test files
        # These might be new source files, documentation, config files etc.
        # Current logic doesn't explicitly add tests for *new* source files
        # unless they come with *new* test files (handled by point 2).
        # If a new source file is added and covered by *existing* tests,
        # the *old* coverage map won't know about it. This is a limitation.
        if not tests_in_file and not is_test_file(file_path):
            logger.warning(
                f"Changed file '{file_path}' is not in the "
                "coverage map and not identified as a test file."
                " No direct tests added for it.",
            )

    if run_all_tests_flag:
        return set()

    return tests_to_run
