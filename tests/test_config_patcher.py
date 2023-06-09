from confz import ConfZ, ConfZDataSource
from pydantic import BaseModel

from flexigurator.config_patch import patch_config


class TestSubModel(BaseModel):
    __test__ = False
    some_string: str


class TestOptionalConfig(ConfZ):  # type: ignore
    __test__ = False
    sub_model: TestSubModel | None

    CONFIG_SOURCES = [ConfZDataSource(dict(sub_model=dict(some_string="string")))]


class TestConfig1(ConfZ):  # type: ignore
    __test__ = False
    sub_model: TestSubModel
    some_int: int
    some_float: float


class TestConfig2(ConfZ):  # type: ignore
    __test__ = False
    sub_model: TestSubModel
    some_int: int
    some_float: float

    CONFIG_SOURCES = ConfZDataSource(dict(
        sub_model=TestSubModel(some_string="old"),
        some_int=1,
        some_float=3.14
    ))


class TestConfig3(ConfZ):  # type: ignore
    __test__ = False
    sub_model: TestSubModel
    some_int: int
    some_float: float

    CONFIG_SOURCES = [
        ConfZDataSource(dict(
            sub_model=TestSubModel(some_string="old"),
        )),
        ConfZDataSource(dict(
            some_int=1,
            some_float=3.14,
        ))
    ]


def test_context():
    data = dict(
        some_int=2,
    )
    with patch_config(TestConfig2, data):
        assert TestConfig2().some_int == 2

    assert TestConfig2().some_int == 1


def test_context_sequential():
    with patch_config(TestOptionalConfig, dict(sub_model=dict(some_string="test"))):
        assert TestOptionalConfig().sub_model.some_string == "test"
    with patch_config(TestOptionalConfig, dict(sub_model=dict(some_string="test2"))):
        assert TestOptionalConfig().sub_model.some_string == "test2"
    with patch_config(TestOptionalConfig, dict(sub_model=None)):
        assert TestOptionalConfig().sub_model is None
    with patch_config(TestOptionalConfig, dict(sub_model=dict(some_string="test3"))):
        assert TestOptionalConfig().sub_model.some_string == "test3"


def test_config_without_sources():
    data = dict(
        sub_model=TestSubModel(some_string="new"),
        some_int=2,
        some_float=4.2
    )
    with patch_config(TestConfig1, data):
        assert TestConfig1().sub_model == data["sub_model"]
        assert TestConfig1().some_int == data["some_int"]
        assert TestConfig1().some_float == data["some_float"]


def test_config_with_sources():
    data = dict(
        sub_model=TestSubModel(some_string="new"),
        some_int=2,
        some_float=4.2
    )
    with patch_config(TestConfig2, data):
        assert TestConfig2().sub_model == data["sub_model"]
        assert TestConfig2().some_int == data["some_int"]
        assert TestConfig2().some_float == data["some_float"]


def test_config_add_partial_data_1():
    data = dict(
        sub_model=TestSubModel(some_string="new"),
        some_int=2,
    )
    with patch_config(TestConfig2, data):
        assert TestConfig2().sub_model == data["sub_model"]
        assert TestConfig2().some_int == data["some_int"]
        assert TestConfig2().some_float == 3.14


def test_config_add_partial_data_2():
    data = dict(
        some_int=2,
        some_float=4.2,
    )
    with patch_config(TestConfig2, data):
        assert TestConfig2().sub_model.some_string == "old"
        assert TestConfig2().some_int == data["some_int"]
        assert TestConfig2().some_float == data["some_float"]


def test_config_add_partial_data_3():
    data = dict(
        some_float=4.2,
    )
    with patch_config(TestConfig2, data):
        assert TestConfig2().sub_model.some_string == "old"
        assert TestConfig2().some_int == 1
        assert TestConfig2().some_float == data["some_float"]


def test_config_data_source():
    data = ConfZDataSource(dict(
        sub_model=TestSubModel(some_string="new"),
        some_int=2,
        some_float=4.2
    ))
    with patch_config(TestConfig2, data):
        assert TestConfig2().sub_model == data.data["sub_model"]
        assert TestConfig2().some_int == data.data["some_int"]
        assert TestConfig2().some_float == data.data["some_float"]


def test_config_multiple_config_sources_1():
    data = ConfZDataSource(dict(
        sub_model=TestSubModel(some_string="new"),
        some_int=2,
        some_float=4.2
    ))
    with patch_config(TestConfig3, data):
        assert TestConfig3().sub_model == data.data["sub_model"]
        assert TestConfig3().some_int == data.data["some_int"]
        assert TestConfig3().some_float == data.data["some_float"]


def test_config_multiple_config_sources_2():
    data = [
        ConfZDataSource(dict(
            sub_model=TestSubModel(some_string="new"),
            some_int=2,
        )),
        ConfZDataSource(dict(
            some_float=4.2
        ))
    ]
    with patch_config(TestConfig3, data):
        assert TestConfig3().sub_model.some_string == "new"
        assert TestConfig3().some_int == 2
        assert TestConfig3().some_float == 4.2
