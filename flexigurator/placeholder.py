from typing import Any, Type

from pydantic import BaseModel
from pydantic.fields import ModelField


class NotConfiguredError(Exception):
    """Raised when a requested configuration variable is not supplied in configuration source."""


class Placeholder:
    _model_type: Type[BaseModel]
    _model_fields: dict[str, ModelField]

    def __init__(self, model_type: Type[BaseModel]):
        self._model_type = model_type
        # Get the fields of the BaseModel
        self._model_fields = model_type.__fields__

    def __getattribute__(self, item: str) -> Any:
        # Get an attribute 'as usual' but raise a `NotConfiguredError` on Model fields.
        try:
            # Check if the requested attribute is part of the BaseModel fields
            fields = object.__getattribute__(self, "_model_fields")
            if item in fields:
                # A BaseModel field is being requested, but as this model is not configured we
                # throw an exception
                raise NotConfiguredError(self._model_type)
        except AttributeError:
            """We cannot check using other means than a try/catch due to recursion."""

        # The requested attribute is not a BaseModel field, so we return the attribute normally
        return object.__getattribute__(self, item)

    def __repr__(self):
        return f"NotConfigured({self._model_type})"


def placeholder(model_type: Type[BaseModel]) -> Any:
    """Return a placeholder set as pydantic field value to make it optionally configurable.

    Specifically this removes the need to use `None` to make fields optional, thereby making
    configuration classes much easier to work with as convoluted `None` checking is no longer
    needed.

    class SomeSubModel(BaseModel):
        some_int: int

    class SomeModel(BaseModel):
        sub_model: SomeSubModel = placeholder(SomeSubModel)

    SomeModel().sub_model.some_int                                    # Raises NotConfiguredError
    SomeModel(sub_model=SomeSubModel(some_int=5)).sub_model.some_int  # Returns 5

    Args:
        model_type (Type[BaseModel]): The type of BaseModel it makes configurable

    Returns:
        Any: A Placeholder object
    """
    return Placeholder(model_type)
