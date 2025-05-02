import ast
from pathlib import Path

import pytest

from skippy_cov.tests_finder import ASTTestsFinder


@pytest.fixture
def module_level_tests_ast() -> ast.Module:
    return ast.parse(
        """
def not_a_test():
    pass

def test_foo():
    pass

def test_parameterized(foo, bar, baz):
    pass

async def test_bar():
    pass"""
    )


@pytest.fixture
def class_level_tests_ast() -> ast.Module:
    return ast.parse(
        """
class TestFoo:
    def not_a_test(self):
        pass

    def test_foo(self):
        pass

    def test_parameterized(self, foo, bar, baz):
        pass

    async def test_bar(self):
        pass"""
    )


@pytest.fixture
def class_level_tests_ast_with_init() -> ast.Module:
    return ast.parse(
        """
class TestFoo:
    def __init__(self):
        pass

    def test_foo(self):
        pass"""
    )


def test_find_top_level_tests(module_level_tests_ast: ast.Module) -> None:
    """
    Test that we can find test functions following basic pytest discovery conventions:
    - Top-level functions `test_*`
    - Top-level async functions `test_*`
    """

    finder = ASTTestsFinder(Path("foo.py"))
    finder.visit(module_level_tests_ast)
    assert finder.tests == {
        "test_foo",
        "test_parameterized",
        "test_bar",
    }


def test_find_class_level_tests(class_level_tests_ast: ast.Module) -> None:
    """
    Test that we can find test methods inside a clase:
    - Methods named `test_*`
    - Async methods named `test_*`
    """

    finder = ASTTestsFinder(Path("foo.py"))
    finder.visit(class_level_tests_ast)
    assert finder.tests == {
        "TestFoo::test_foo",
        "TestFoo::test_parameterized",
        "TestFoo::test_bar",
    }


def test_do_not_find_tests_in_init(class_level_tests_ast_with_init: ast.Module) -> None:
    """
    Test that we don't find tests in classes with an `__init__` method
    """
    finder = ASTTestsFinder(Path("foo.py"))
    finder.visit(class_level_tests_ast_with_init)
    assert finder.tests == set()
