from pathlib import Path
from typing import Callable, Generator

import pytest
from pytest_mock import MockFixture

from skippy_cov import config_handler


@pytest.fixture
def pytest_ini():
    return """[pytest]
addopts = "--cov"
pythonpath = "/src"
"""


@pytest.fixture
def pyproject_toml():
    return """[tool.pytest.ini_options]
addopts = "--cov"
pythonpath = "/src"
"""


@pytest.fixture
def setup_cfg():
    return """[tool:pytest]
addopts = "--cov"
pythonpath = "/src"
"""


GetConfigFun = Callable[[], config_handler.ConfigHandler]


@pytest.fixture
def get_config() -> Generator[GetConfigFun, None, None]:
    yield lambda: config_handler.get_config()
    config_handler._config = None  # reset borg


def test_config_handler_presedence(get_config: GetConfigFun, mocker: MockFixture):
    """
    Test that .pytest.ini has the highest priority regardless of order
    """
    mocker.patch(
        "skippy_cov.config_handler.Path.iterdir",
        return_value=[
            Path("setup.cfg"),
            Path("tox.ini"),
            Path("pyproject.toml"),
            Path("pytest.ini"),
        ],
    )
    _ = mocker.patch("skippy_cov.config_handler.Path.read_text", return_value="")
    cfg = get_config()
    assert bool(cfg)
    assert cfg.handler
    assert cfg.handler.config_path.name == "pytest.ini"


@pytest.mark.parametrize(
    "config_name,config_fixture",
    [
        ("pytest.ini", "pytest_ini"),
        (".pytest.ini", "pytest_ini"),
        ("tox.ini", "pytest_ini"),
        ("pyproject.toml", "pyproject_toml"),
        ("setup.cfg", "setup_cfg"),
    ],
)
def test_config_handler_parser(
    config_name: str,
    config_fixture: str,
    get_config: GetConfigFun,
    mocker: MockFixture,
    request,
):
    mocker.patch(
        "skippy_cov.config_handler.Path.iterdir",
        return_value=[Path(config_name)],
    )

    mocker.patch(
        "skippy_cov.config_handler.Path.read_text",
        return_value=request.getfixturevalue(config_fixture),
    )
    assert config_handler._config is None  # sanity check
    cfg = get_config()
    assert cfg.get_value("addopts") == '"--cov"'
    assert cfg.get_value("pythonpath") == '"/src"'


def test_config_handler_no_config_found(mocker: MockFixture, get_config: GetConfigFun):
    mocker.patch(
        "skippy_cov.config_handler.Path.iterdir",
        return_value=[],
    )
    mocker.patch("skippy_cov.config_handler.Path.parents", return_value=[])
    cfg = get_config()
    assert not bool(cfg)


def test_config_handler_no_config_no_value(
    mocker: MockFixture,
    get_config: GetConfigFun,
):
    mocker.patch(
        "skippy_cov.config_handler.Path.iterdir",
        return_value=[],
    )
    mocker.patch("skippy_cov.config_handler.Path.parents", return_value=[])
    cfg = get_config()
    assert cfg.get_value("addopts") is None
