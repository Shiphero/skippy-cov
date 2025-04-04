from __future__ import annotations

from pytest_mock import MockerFixture

from skippy_cov import discover_tests_in_file


def test_discover_tests_in_file(mocker: MockerFixture) -> None:
    mocker.patch("skippy_cov.is_test_file", return_value=True)
    mock = mocker.MagicMock()
    mock.read_text.return_value = "def test_foo(): pass\ndef test_bar(): pass"
    mock.is_file.return_value = True
    mock.exists.return_value = True
    mock.name = "test_file.py"
    result = discover_tests_in_file(mock)
    assert result == ["test_file.py::test_foo", "test_file.py::test_bar"]
