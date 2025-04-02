from pathlib import Path

import pytest

from skippy_cov.diff_handler import DiffHandler, DiffHandlerError


@pytest.fixture
def foo_hunk() -> str:
    return """--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,1 @@
 def foo():
-    return 1"""


@pytest.fixture
def bar_hunk() -> str:
    return """--- a/bar.py
+++ b/bar.py
@@ -1,2 +1,1 @@
 def bar():
-    return 1"""


@pytest.fixture
def invalid_hunk() -> str:
    """
    Hunk is invalid because it doesn't have a diff
    """

    return """--- a/invalid.py
+++ b/invalid.py
@@ -1 +1 @@
"""


@pytest.fixture
def text_diff(foo_hunk: str, bar_hunk: str) -> str:
    return f"{foo_hunk}\n{bar_hunk}"


@pytest.fixture
def diff_handler(text_diff: str) -> DiffHandler:
    return DiffHandler(text_diff)


def test_changed_files(diff_handler: DiffHandler) -> None:
    """
    Test that the diff handler correctly identifies the changed files
    """
    assert len(diff_handler.changed_files) == 2
    assert Path("foo.py") in diff_handler.changed_files
    assert Path("bar.py") in diff_handler.changed_files


def test_get_contents(diff_handler: DiffHandler, foo_hunk: str, bar_hunk: str) -> None:
    """
    Test that the diff handler correctly returns the contents of the changed files
    """
    assert diff_handler[Path("foo.py")] == foo_hunk
    assert diff_handler[Path("bar.py")] == bar_hunk


def test_invalid_hunk(invalid_hunk: str) -> None:
    """
    Test that the diff handler raises an error for invalid hunks

    It's not common to encounter invalid hunks when using 'git diff',
        but we react to it nontheless
    """
    with pytest.raises(DiffHandlerError):
        DiffHandler(invalid_hunk)
