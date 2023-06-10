from flexigurator import placeholder, NotConfiguredError
from pydantic import BaseModel

import pytest


class TestSubModel(BaseModel):
    __test__ = False
    some_string: str


class TestModel(BaseModel):
    __test__ = False
    sub_model: TestSubModel = placeholder(TestSubModel)


def test_placeholder_crash_on_request_parameter():
    with pytest.raises(NotConfiguredError):
        TestModel().sub_model.some_string


def test_placeholder_succeed_when_configured():
    model = TestModel(sub_model=TestSubModel(some_string="test"))
    assert model.sub_model.some_string == "test"


def test_placeholder_repr():
    actual = repr(TestModel().sub_model)
    assert "NotConfigured" in actual and "TestSubModel" in actual


def test_placeholder_dict():
    actual = TestModel().sub_model.dict()
    assert actual == {}
