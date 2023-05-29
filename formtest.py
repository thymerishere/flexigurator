from pathlib import Path
from flexigurator import placeholder
from flexigurator.form.form import ConfigForm
from pydantic import BaseModel

class SubSubModel(BaseModel):
    some_str: str


class SubModel(BaseModel):
    some_int: int
    nother: SubSubModel = placeholder(SubSubModel)


class Model(BaseModel):
    sub_model: SubModel = placeholder(SubModel)
    # rand_int: int
    # rand_str: str



app = ConfigForm(
    Model,
    Path("./save"),
    Path("./templates"),
    Path("flexigurator/form/jinja_templates"),
)
