from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import reduce
from pathlib import Path
from typing import Any, Mapping, Type, TypeVar

from confz import ConfZ, ConfZDataSource, ConfZFileSource, ConfZSource

from flexigurator.config_patch import patch_config

ConfigSource = ConfZSource | list[ConfZSource]


T = TypeVar("T")


def _flatten(a: T | list[T], b: T | list[T]) -> list[T]:
    joined = [a] + [b]

    def expand(agg: list[T], item: T | list[T]) -> list[T]:
        if isinstance(item, list):
            return agg + item
        return agg + [item]

    result = reduce(expand, joined, [])  # type: ignore
    return result  # type: ignore


def is_config_source(source: Any):
    return (
        isinstance(source, ConfZSource)
        or (isinstance(source, dict) and all(isinstance(key, str) for key in source))
        or (isinstance(source, list) and all(isinstance(item, ConfZSource) for item in source))
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
            if sub_path.suffix == ".yaml":
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
    """Hold various versions of configurations that can be loaded in a context manager.

    One should implement this class in a config versions class (e.g. `Configs`). Fields pointing to
    `ConfZSource`s, `DirectorySource`s, or dictionaries can then be added to load configuration
    versions. These versions can then be loaded using `Configs.version` as a context manager.

    Example:
        class Config(ConfZ):  # type: ignore
            a: int
            b: int

        class Configs(ConfigVersions):
            CONFIG_CLASS = Config
            BASE = dict(a=1, b=2)  # Optional base version which is loaded before other versions
            test = ConfZFileSource("configs/test.yaml")

        with Configs().version("test"):
            print(Config())  # Configuration from the ConfZFileSource is now loaded

    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_sources(self) -> None:
        pass

    @contextmanager
    def version(self, version_name: str, config_class: Type[ConfZ] | None = None):
        """Select a version from the collection and patch the supplied config class.

        Args:
            version_name (str): The name of the configuration version (i.e. the field name)
            config_class (Type[ConfZ]): The configuration class to patch

        Yields:
            ...

        Raises:
            AttributeError: When no config class is given or the version does not exist
        """
        config_class = config_class or getattr(self, "CONFIG_CLASS", None)

        if not config_class:
            raise AttributeError(
                'Need to supply "config_class" as parameter or "CONFIG_CLASS" in ConfigVersions!'
            )

        version_sources = self.get(version_name)

        if hasattr(self, "BASE"):
            version_base = self.get("BASE")
            version_sources = _flatten(version_base, version_sources)

        with patch_config(config_class, version_sources):
            yield
