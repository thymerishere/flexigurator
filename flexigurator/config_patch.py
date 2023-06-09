from contextlib import contextmanager
from typing import Any, Iterator, Type

from confz import ConfZ, ConfZDataSource, ConfZSource


@contextmanager
def patch_config(
    config_class: Type[ConfZ], data: dict[str, Any] | ConfZSource | list[ConfZSource]
) -> Iterator[None]:
    """Patch a config class with additional sources.

    This context manager temporarily updates the given config class with the provided data sources.
    This is useful for testing where a specific set of configuration values needs to be changed for
    a single test instance. Importantly, the provided configuration does not need to be complete,
    as long as the original configuration sources are.

    Args:
        config_class (Type[ConfZ]): The ConfZ config class
        data (dict[str, Any] | ConfZSource | list[ConfZSource]): A source of configuration in the
            form of a dictionary or one or more ConfZ sources

    Yields:
        None: This context manager does not yield

    """
    if isinstance(data, dict):
        data = ConfZDataSource(data)

    if not isinstance(data, list):
        data = [data]

    original_sources = config_class.CONFIG_SOURCES
    patched_sources: list[ConfZSource]

    if original_sources is None:
        patched_sources = []
    elif not isinstance(original_sources, list):
        patched_sources = [original_sources]
    else:
        patched_sources = list(original_sources)

    patched_sources += data

    with config_class.change_config_sources(patched_sources):
        yield
