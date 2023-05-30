import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type

import mmh3
import yaml
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


@dataclass
class ConfigTemplate:
    uid: str
    name: str
    path: Path

    @staticmethod
    def from_path(path: Path, templates_path: Path):
        # Create the name from the path by taking its path relative to the templates dir and
        # removing the suffix (e.g. '.yaml')
        # '/home/test/gridshield-python/configs/templates/sender/module.yaml' -> 'sender/module'
        name = os.path.splitext(path.relative_to(templates_path))[0]
        uid = str(mmh3.hash(name, signed=False))
        return ConfigTemplate(uid=uid, name=name, path=path)


def _load_config_templates(path: Path) -> list[ConfigTemplate]:
    templates = [ConfigTemplate.from_path(file_path, path) for file_path in path.glob("**/*.yaml")]
    templates = sorted(templates, key=lambda template: template.name)

    return templates


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r") as yaml_file:
        yaml_file_contents = yaml_file.read()

    yaml_object = yaml.safe_load(yaml_file_contents)

    return yaml_object if yaml_object else {}


def _config_form_start_vals(uid: str, config_templates: list[ConfigTemplate]) -> str:
    path = [template for template in config_templates if template.uid == uid][0].path
    return json.dumps(_load_yaml(path))


def _write_to_file(file_path: Path, contents: str) -> None:
    with open(file_path, "w") as file:
        file.write(contents)


def _save_config_form_output(json_: dict[str, Any], file_name: str, save_path: Path):
    if json_ == {}:
        yaml_str = ""
    else:
        yaml_str = yaml.dump(json_)

    yaml_file_path = save_path.joinpath(Path(file_name + ".yaml"))
    yaml_file_path.parent.mkdir(parents=True, exist_ok=True)
    _write_to_file(yaml_file_path, yaml_str)


def ConfigForm(
    config: Type[BaseModel],
    config_save_path: Path,
    config_templates_path: Path,
    jinja_templates_path: Path,
) -> FastAPI:  # pragma: no cover
    app = FastAPI()
    templates = Jinja2Templates(directory=jinja_templates_path)
    config_templates = _load_config_templates(config_templates_path)
    schema = config.schema()

    @app.get("/", response_model=None)
    async def root(request: Request) -> Response:
        template_dict = {template.uid: template.name for template in config_templates}

        return templates.TemplateResponse(
            "index.html", {"request": request, "template_names": template_dict}
        )

    @app.get("/config_template/{uid}", response_model=None)
    async def config_form(request: Request, uid: str) -> Response:
        return templates.TemplateResponse(
            "config_form.html",
            {
                "request": request,
                "schema_json": schema,
                "start_val": _config_form_start_vals(uid, config_templates),
            },
        )

    @app.post("/config_json/{file_name}", response_model=None)
    async def _config_json(request: Request, file_name: str) -> dict[str, str]:
        json_ = await request.json()
        _save_config_form_output(json_, file_name, config_save_path)
        return {"message": f"Parsed config json {json_}!"}

    return app
