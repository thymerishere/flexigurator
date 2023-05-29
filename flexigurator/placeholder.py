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
        self._model_fields = model_type.__fields__  # type: ignore

    def __getattribute__(self, item: str) -> Any:
        """Usual getting an attribute but raises `NotConfiguredError` on Model fields."""
        try:
            # Check if the requested attribute is part of the BaseModel fields
            fields = object.__getattribute__(self, "_model_fields")
            if item in fields:
                # A BaseModel field is being requested, which is not possible as it is not
                # configured, so we throw an exception
                raise NotConfiguredError(self._model_type)
        except AttributeError:
            """We cannot check using other means than a try/catch due to recursion."""

        # The requested attribute is not a BaseModel field, so we return the attribute normally
        return object.__getattribute__(self, item)

    def __repr__(self):
        return f"NotConfigured({self._model_type})"


def placeholder(model_type: Type[BaseModel]) -> Any:
    return Placeholder(model_type)
