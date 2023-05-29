from pathlib import Path
from flexigurator.form.form import ConfigForm
from pydantic import BaseModel

class Model(BaseModel):
    a: int = 5


app = ConfigForm(
    Model,
    Path("./save"),
    Path("./templates"),
    Path("flexigurator/form/jinja_templates"),
)
