import os
import tempfile
from pathlib import Path

import pytest
from confz import ConfZ, ConfZDataSource
from pydantic import BaseModel

from flexigurator.config_versions import ConfigVersions, DirectorySource


class TestSubModel(BaseModel):
    __test__ = False
    some_string: str


class TestOptionalConfig(ConfZ):  # type: ignore
    __test__ = False
    sub_model: TestSubModel | None


class MultiFieldConfig(ConfZ):  # type: ignore
    __test__ = False
    a: int
    b: int


def test_config_versions():
    class Configs(ConfigVersions):
        CONFIG_CLASS = TestOptionalConfig
        test = dict(sub_model=dict(some_string="string"))

    with Configs().version("test"):
        assert TestOptionalConfig().sub_model.some_string == "string"


def test_config_versions_folder():
    class Configs(ConfigVersions):
        CONFIG_CLASS = TestOptionalConfig
        test = [
            ConfZDataSource(dict(sub_model=dict(some_string="test"))),
            ConfZDataSource(dict(sub_model=dict(some_string="test_1"))),
            ConfZDataSource(dict(sub_model=dict(some_string="test_2"))),
        ]

    with Configs().version("test"):
        assert TestOptionalConfig().sub_model.some_string == "test_2"


def test_config_versions_multiple():
    class Configs(ConfigVersions):
        CONFIG_CLASS = TestOptionalConfig
        test1 = dict(sub_model=dict(some_string="string"))
        test2 = dict(sub_model=dict(some_string="also_string"))
        test3 = dict(sub_model=dict(some_string="also_also_string"))

    with Configs().version("test1"):
        assert TestOptionalConfig().sub_model.some_string == "string"
    with Configs().version("test2"):
        assert TestOptionalConfig().sub_model.some_string == "also_string"
    with Configs().version("test3"):
        assert TestOptionalConfig().sub_model.some_string == "also_also_string"


def test_config_versions_config_class_as_parameter():
    class Configs(ConfigVersions):
        test = dict(sub_model=dict(some_string="string"))

    with Configs().version("test", TestOptionalConfig):
        assert TestOptionalConfig().sub_model.some_string == "string"


def test_config_versions_raise_when_no_config_class():
    class Configs(ConfigVersions):
        test = dict(sub_model=dict(some_string="string"))

    with pytest.raises(AttributeError):
        with Configs().version("test"):
            ...


def test_config_versions_raise_when_source_doesnt_exist():
    class Configs(ConfigVersions):
        CONFIG_CLASS = TestOptionalConfig
        test = dict(sub_model=dict(some_string="string"))

    with pytest.raises(AttributeError):
        with Configs().version("no_test"):
            ...


def test_config_versions_raise_when_version_is_not_config_source():
    class Configs(ConfigVersions):
        CONFIG_CLASS = TestOptionalConfig
        test_1 = 5
        test_2 = "string"
        test_3 = None

    with pytest.raises(AttributeError):
        with Configs().version("test_1"):
            ...

    with pytest.raises(AttributeError):
        with Configs().version("test_2"):
            ...

    with pytest.raises(AttributeError):
        with Configs().version("test_3"):
            ...


def test_config_versions_base():

    class Configs(ConfigVersions):
        CONFIG_CLASS = MultiFieldConfig
        BASE = dict(a=1, b=2)
        test = dict(a=3)

    with Configs().version("BASE"):
        assert MultiFieldConfig().a == 1
        assert MultiFieldConfig().b == 2

    with Configs().version("test"):
        assert MultiFieldConfig().a == 3
        assert MultiFieldConfig().b == 2


def test_config_base_folder():
    class Configs(ConfigVersions):
        CONFIG_CLASS = TestOptionalConfig
        BASE = [
            ConfZDataSource(dict(sub_model=dict(some_string="test"))),
            ConfZDataSource(dict(sub_model=dict(some_string="test_1"))),
        ]
        test = [
            ConfZDataSource(dict(sub_model=dict(some_string="test_1"))),
            ConfZDataSource(dict(sub_model=dict(some_string="test_2"))),
        ]

    with Configs().version("test"):
        assert TestOptionalConfig().sub_model.some_string == "test_2"



def test_config_versions_base_incomplete():

    class Configs(ConfigVersions):
        CONFIG_CLASS = MultiFieldConfig
        BASE = dict(b=2)
        test = dict(a=3)

    with Configs().version("test"):
        assert MultiFieldConfig().a == 3
        assert MultiFieldConfig().b == 2


def test_directory_source():
    config_a = """a: 1\nb: 2"""
    config_b = """a: 2\nb: 4"""
    config_c = """a: 4\nb: 8"""

    with tempfile.TemporaryDirectory(dir=".") as temp_dir:
        with open(temp_dir + "/config_a.yaml", "w") as file:
            file.write(config_a)
        with open(temp_dir + "/config_b.yaml", "w") as file:
            file.write(config_b)
        os.mkdir(temp_dir + "/nested")
        with open(temp_dir + "/nested/config_c.yaml", "w") as file:
            file.write(config_c)

        class DirectoryConfigs(ConfigVersions):
            CONFIG_CLASS = MultiFieldConfig
            folder = DirectorySource(Path(temp_dir))

        with DirectoryConfigs().version("folder.config_a"):
            assert MultiFieldConfig().a == 1
            assert MultiFieldConfig().b == 2
        with DirectoryConfigs().version("folder.config_b"):
            assert MultiFieldConfig().a == 2
            assert MultiFieldConfig().b == 4
        with DirectoryConfigs().version("folder.nested.config_c"):
            assert MultiFieldConfig().a == 4
            assert MultiFieldConfig().b == 8


def test_directory_source_raise_when_getting_folder():
    config_a = """a: 1\nb: 2"""
    config_b = """a: 2\nb: 4"""
    config_c = """a: 4\nb: 8"""

    with tempfile.TemporaryDirectory(dir=".") as temp_dir:
        with open(temp_dir + "/config_a.yaml", "w") as file:
            file.write(config_a)
        with open(temp_dir + "/config_b.yaml", "w") as file:
            file.write(config_b)
        os.mkdir(temp_dir + "/nested")
        with open(temp_dir + "/nested/config_c.yaml", "w") as file:
            file.write(config_c)

        class DirectoryConfigs(ConfigVersions):
            CONFIG_CLASS = MultiFieldConfig
            folder = DirectorySource(Path(temp_dir))

        with pytest.raises(ValueError):
            with DirectoryConfigs().version("folder"):
                ...

        with pytest.raises(ValueError):
            with DirectoryConfigs().version("folder.nested"):
                ...
