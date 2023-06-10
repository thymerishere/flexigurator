from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping, Type, get_args

from confz import ConfZ, ConfZDataSource, ConfZFileSource, ConfZSource

from flexigurator import patch_config

ConfigSource = ConfZSource | list[ConfZSource]


def is_config_source(source: Any):
    if source is None:
        return False

    return (
        isinstance(source, ConfZSource)
        or (isinstance(source, dict) and get_args(type(source))[0] == str)
        or (isinstance(source, list) and get_args(type(source)) == (ConfZSource,))
    )


class _VersionCollection(ABC):
    """Hold a collection of configuration versions."""

    @abstractmethod
    def _load_sources(self) -> None:
        """Lazily load the config version sources."""

    def get(self, version_name: str) -> ConfigSource:
        self._load_sources()

        version_name_split = version_name.split(".", maxsplit=1)
        source_name = version_name_split[0]

        source = getattr(self, source_name, None)

        if not source:
            raise AttributeError(f"Version source does not exist: {source_name}")

        if isinstance(source, _VersionCollection):
            if len(version_name_split) != 2:
                raise ValueError(f'"{source_name}" is a collection!')

            return source.get(version_name_split[1])

        if isinstance(source, dict):
            return ConfZDataSource(source)

        if not is_config_source(source):
            raise AttributeError(f"Not a version source: {source_name}")

        return source  # type: ignore


class DirectorySource(_VersionCollection):
    """Hold a collection of version sources located in a folder.

    Args:
        path (Path): Path to the folder containing the `.yaml` configuration files

    """

    _path: Path

    def __init__(self, path: Path):
        super().__init__()
        self._path = path

    def _load_sources(self) -> None:
        self._set_versions(self._load_versions(self._path))

    @staticmethod
    def _load_versions(path: Path) -> Mapping[str, ConfZFileSource | DirectorySource]:
        versions = dict[str, ConfZFileSource | DirectorySource]()
        for sub_path in path.glob("*"):
            if path.suffix == ".yaml":
                name = sub_path.stem
                versions[name] = ConfZFileSource(sub_path)
            if sub_path.is_dir():
                name = sub_path.name
                versions[name] = DirectorySource(sub_path)
        return versions

    def _set_versions(self, configs: Mapping[str, ConfigSource | DirectorySource]) -> None:
        for name, version_source in configs.items():
            setattr(self, name, version_source)


class ConfigVersions(_VersionCollection):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Set the default configuration version
        if (default := getattr(self, "default", None)) is not None and (
            config_class := getattr(self, "CONFIG_CLASS", None)
        ) is not None:
            if not is_config_source(default):
                raise AttributeError("Not a version source: default")
            config_class.CONFIG_SOURCES = default

    def _load_sources(self) -> None:
        pass

    @contextmanager
    def version(self, version_name: str, config_class: Type[ConfZ] | None = None):
        config_class = config_class or getattr(self, "CONFIG_CLASS", None)

        if not config_class:
            raise AttributeError('Need to supply "config_class" as parameter or in ConfigVersions!')

        version_sources = self.get(version_name)

        with patch_config(config_class, version_sources):
            yield
