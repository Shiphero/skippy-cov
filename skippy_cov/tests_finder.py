from __future__ import annotations

import ast
from pathlib import Path


class ASTTestsFinder(ast.NodeVisitor):
    """
    Visits an AST tree and collects test functions and methods
    following basic pytest discovery conventions:
    - Top-level functions `test_*`
    - Classes `Test*` containing methods `test_*`
        - Classes with an `__init__` method are ignored
    See: https://docs.pytest.org/en/latest/explanation/goodpractices.html#conventions-for-python-test-discovery
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.tests: set[str] = set()
        self.current_class_name: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit Class Definitions."""

        # TODO: consider python_classes and python_functions parameters on config
        # SEE: https://docs.pytest.org/en/stable/example/pythoncollection.html#changing-naming-conventions
        class_has_init_method = any(
            hasattr(method, "name") and method.name == "__init__" for method in node.body
        )
        if node.name.startswith("Test") and not class_has_init_method:
            original_class_name = self.current_class_name
            self.current_class_name = node.name
            self.generic_visit(node)
            self.current_class_name = original_class_name
        else:
            pass

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Visit Function (and Method) Definitions."""

        # TODO: consider python_classes and python_functions parameters on config
        # SEE: https://docs.pytest.org/en/stable/example/pythoncollection.html#changing-naming-conventions
        if node.name.startswith("test_"):
            if self.current_class_name:
                test_id = f"{self.current_class_name}::{node.name}"
                self.tests.add(test_id)
            else:
                test_id = node.name
                self.tests.add(test_id)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit Async Function (and Method) Definitions."""
        return self.visit_FunctionDef(node)
