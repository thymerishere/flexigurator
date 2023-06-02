# Flexigurator

**Flexigurator** is a collection of useful tools when working with configuration.
Flexigurator builds on top of [ConfZ](https://confz.readthedocs.io/en/latest/) and [Pydantic](https://docs.pydantic.dev/latest/)
while adding some extra functionality to make your life easier when testing and deploying.


## Examples

### `config_patch`
When using ConfZ to define a configuration singleton using a `.yaml` file,

```yaml
# config.yaml
some_string: default
some_int: 42
```


```python
from confz import ConfZ, ConfZFileSource

class Config(ConfZ):
    some_string: str
    some_int: int

    CONFIG_SOURCES = ConfZFileSource("config.yaml")
```

configuration variables can be easily hotswapped using `patch_config`:

```python
from flexigurator import patch_config


data = dict(some_int=9001)


with patch_config(Config, data):
    Config().some_int     # 9001

    
Config().some_int     # 42
```

Importantly, the new data does not need to be complete.


### `placeholder`
When having nested, optional `BaseModel`s in your `Config`,

```python
class Config(ConfZ):
    ui: UIConfig | None
    server: ServerConfig | None    
```

it would be nice if trying to load configuration automatically throws an exception if it is not configured.
The `placeholder` method provides such functionality, and it can be used as follows:

```python
from flexigurator import placeholder, patch_config


class Config(ConfZ):
    ui: UIConfig = placeholder(UIConfig)
    server: ServerConfig = placeholder(UIConfig)
    

Config().server.ip_address  # NotConfiguredException!
```

This removes the need for `None`-checking as exception handling is done behind the scenes.


### `ConfigForm`
`ConfigForm` allows for the easy creation of forms for `ConfZ` or `BaseModel` classes.
Forms are generated using [Json Editor](https://github.com/json-editor/json-editor) and are served using [FastAPI](https://fastapi.tiangolo.com).
Having instantiated `ConfigForm`,

```python
# form.py
from flexigurator import ConfigForm


app = ConfigForm(Config, "save/path", "templates/path")
```

The server can be started using (for instance) [Uvicorn](https://www.uvicorn.org):

```bash
uvicorn form:app
```


## Installation
Flexigurator is available on [PyPi](https://pypi.org/project/flexigurator/0.3.0/#description) and can be installed using pip:

```bash
pip install flexigurator
```
