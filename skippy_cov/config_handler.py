from __future__ import annotations

import configparser
from enum import Enum
from pathlib import Path
from typing import ClassVar

try:
    import tomllib
except ImportError:
    import tomli as tomllib


_config: ConfigHandler | None = None


def get_config(base_location: Path) -> ConfigHandler:
    global _config
    if not _config:
        _config = ConfigHandler(base_location)
    return _config


class ConfigFormat(Enum):
    INI = "ini"
    TOML = "toml"


class ConfigFileHandler:
    values: dict[str, str] | None = None
    section_name: str
    parser: ConfigFormat

    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self._parse()

    def _parse(self) -> None:
        if self.parser == ConfigFormat.INI:
            self._parse_ini()
        elif self.parser == ConfigFormat.TOML:
            self._parse_toml()
        else:
            raise NotImplementedError(f"Unsupported {self.parser}")

    def _parse_ini(self) -> None:
        config = configparser.ConfigParser()
        config.read_string(self.config_path.read_text())

        cfgdict = {s: dict(config.items(s)) for s in config.sections()}
        self.values = cfgdict.get(self.section_name, None)

    def _parse_toml(self) -> None:
        config = tomllib.loads(self.config_path.read_text())
        self.values = config.get(self.section_name, None)


class IniHandler(ConfigFileHandler):
    section_name = "pytest"
    parser = ConfigFormat.INI


class SetupCfgHandler(IniHandler):
    section_name = "tool:pytest"
    parser = ConfigFormat.INI


class PyprojectTomlHandler(ConfigFileHandler):
    section_name = "tool.pytest.ini_options"
    parser = ConfigFormat.INI


class ConfigHandler:
    configs: ClassVar[dict[str, type[ConfigFileHandler]]] = {
        "pytest.ini": IniHandler,
        ".pytest.ini": IniHandler,
        "pyproject.toml": PyprojectTomlHandler,
        "tox.ini": IniHandler,
        "setup.cfg": SetupCfgHandler,
    }
    config_priority: ClassVar[list[str]] = [
        "pytest.ini",
        ".pytest.ini",
        "pyproject.toml",
        "tox.ini",
        "setup.cfg",
    ]

    handler: ConfigFileHandler | None

    def __init__(self, base_location: Path):
        self.handler = self._discover_config(base_location)

    def __bool__(self) -> bool:
        return bool(self.handler)

    def get_value(self, key: str) -> str | int | list[str] | None:
        if not self.handler or not self.handler.values:
            return None
        return self.handler.values.get(key)

    def _discover_config(self, base: Path) -> ConfigFileHandler | None:
        """
        Find config files in current or any parent directory
            and return a ConfigFileHandler for the corresponding format
        looks for the following (in order of preference):
            - pytest.ini
            - pyproject.toml
            - tox.ini
            - setup.cfg

            see: https://docs.pytest.org/en/stable/reference/customize.html#configuration-file-formats
        """
        for current in [base, *base.absolute().parents]:
            config = {
                path.name for path in current.iterdir() if path.name in self.configs
            }
            if config:
                top_config = sorted(config, key=self.config_priority.index)[0]
                cls = self.configs[top_config]
                cfg_path = current / top_config
                return cls(cfg_path)
        return None
