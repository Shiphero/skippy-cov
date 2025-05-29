import os
import subprocess

import pytest

from skippy_cov.__main__ import main


@pytest.fixture
def dummy_diff_file(tmp_path):
    diff_content = """diff --git a/foo.py b/foo.py
index e69de29..4b825dc 100644
--- a/foo.py
+++ b/foo.py
@@ -0,0 +1,2 @@
+def foo():
+    return 42
"""
    diff_file = tmp_path / "changes.diff"
    diff_file.write_text(diff_content)
    return diff_file, diff_content


@pytest.fixture
def dummy_coverage_file(tmp_path):
    # Create an empty file for now; actual coverage parsing is not tested here
    cov_file = tmp_path / ".coverage"
    cov_file.write_text("")
    return cov_file


def test_diff_file_mode(dummy_diff_file, dummy_coverage_file, capsys):
    diff_file, _ = dummy_diff_file
    cov_file = dummy_coverage_file
    argv = [
        "--diff",
        str(diff_file),
        "--coverage-file",
        str(cov_file.resolve()),
    ]
    try:
        main(argv)
        code = 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    out = capsys.readouterr()
    assert code == 0, out
    assert "skippy-cov:" not in out.err


def test_diff_git_branch_mode(tmp_path, dummy_coverage_file, capsys):
    # Set up a minimal git repo with a main branch and a change
    import subprocess

    repo = tmp_path
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    (repo / "foo.py").write_text("def foo():\n    return 1\n")
    subprocess.run(["git", "add", "foo.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    # Create a new branch and make a change
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=repo, check=True)
    (repo / "foo.py").write_text("def foo():\n    return 2\n")
    subprocess.run(["git", "add", "foo.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "change"], cwd=repo, check=True)
    cov_file = dummy_coverage_file
    argv = [
        "--diff",
        "main",
        "--coverage-file",
        str(cov_file.resolve()),
    ]
    old_cwd = os.getcwd()
    try:
        os.chdir(repo)
        # Get the actual diff using triple-dot
        actual_diff = subprocess.check_output(["git", "diff", "main...HEAD"], text=True)
        assert "-    return 1" in actual_diff
        assert "+    return 2" in actual_diff
        try:
            main(argv)
            code = 0
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    finally:
        os.chdir(old_cwd)
    out = capsys.readouterr()
    assert code == 0
    assert "skippy-cov:" not in out.err


def test_diff_default_branch(tmp_path, dummy_coverage_file, capsys):
    # Set up a minimal git repo with a main branch and a change
    repo = tmp_path
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    (repo / "bar.py").write_text("def bar():\n    return 1\n")
    subprocess.run(["git", "add", "bar.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    # Create a new branch and make a change
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=repo, check=True)
    (repo / "bar.py").write_text("def bar():\n    return 2\n")
    subprocess.run(["git", "add", "bar.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "change"], cwd=repo, check=True)
    cov_file = dummy_coverage_file
    argv = [
        "--coverage-file",
        str(cov_file.resolve()),
    ]
    old_cwd = os.getcwd()
    try:
        os.chdir(repo)
        try:
            main(argv)
            code = 0
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    finally:
        os.chdir(old_cwd)
    out = capsys.readouterr()
    assert code == 0, out
    assert "skippy-cov:" not in out.err
