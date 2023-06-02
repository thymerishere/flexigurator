from pathlib import Path
import tempfile
from unittest.mock import MagicMock

from flexigurator.form.form import (
    ConfigTemplate,
    _config_form_start_vals,
    _load_config_templates,
    _load_yaml,
    _save_config_form_output,
)
from pytest_mock import MockerFixture


def test_load_config_templates(mocker: MockerFixture):
    with tempfile.TemporaryDirectory(
        dir="./",
    ) as folder_name:
        folder_path = Path(folder_name)

        files = [
            "config_one.yaml",
            "config_two.yaml",
            "nested/config_three.yaml",
            "nested/also_nested/config_four.yaml",
        ]

        file_paths = [folder_path.joinpath(Path(file_name)) for file_name in files]

        for file_path in file_paths:
            file_path.parent.mkdir(exist_ok=True, parents=True)
            open(file_path, "w+")

        hash_mock = MagicMock()
        hash_mock.hash.side_effect = ["1", "2", "3", "4"]
        mocker.patch("flexigurator.form.form.mmh3", hash_mock)

        expected = [
            ConfigTemplate("1", "config_one", folder_path.joinpath(Path("config_one.yaml"))),
            ConfigTemplate("2", "config_two", folder_path.joinpath(Path("config_two.yaml"))),
            # Glob returns in alphabetical order
            ConfigTemplate(
                "3",
                "nested/also_nested/config_four",
                folder_path.joinpath(Path("nested/also_nested/config_four.yaml")),
            ),
            ConfigTemplate(
                "4", "nested/config_three", folder_path.joinpath(Path("nested/config_three.yaml"))
            ),
        ]

        actual = _load_config_templates(folder_path)

    assert actual == expected


def test_load_yaml():
    yaml_str = """
    a: 5
    b: 6
    c: test
    """

    expected = {"a": 5, "b": 6, "c": "test"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as temp_yaml:
        temp_yaml.write(yaml_str)
        temp_yaml.flush()
        file_path = Path(temp_yaml.name)

        actual = _load_yaml(file_path)

    assert actual == expected


def test_load_yaml_empty():
    expected = {}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as temp_yaml:
        file_path = Path(temp_yaml.name)
        actual = _load_yaml(file_path)

    assert actual == expected


def test_save_config_form_output():
    json_ = dict(a=1, b=2, c="test", d=dict(some_int=42))
    file_name = "test"

    expected = ["a: 1\n", "b: 2\n", "c: test\n", "d:\n", "  some_int: 42\n"]

    with tempfile.TemporaryDirectory(
        dir="./",
    ) as folder_name:
        folder_path = Path(folder_name)
        _save_config_form_output(json_, file_name, folder_path)

        with open(folder_path.joinpath(Path(file_name + ".yaml")), "r") as actual_file:
            actual = actual_file.readlines()

    assert actual == expected


def test_save_config_form_output_json_empty():
    json_ = {}
    file_name = "test"

    expected = []

    with tempfile.TemporaryDirectory(
        dir="./",
    ) as folder_name:
        folder_path = Path(folder_name)
        _save_config_form_output(json_, file_name, folder_path)

        with open(folder_path.joinpath(Path(file_name + ".yaml")), "r") as actual_file:
            actual = actual_file.readlines()

    assert actual == expected


def test_config_form_start_vals():
    json_ = dict(a=1, b=2, c="test", d=dict(some_int=42))
    expected = '{"a": 1, "b": 2, "c": "test", "d": {"some_int": 42}}'

    with tempfile.TemporaryDirectory(
        dir="./",
    ) as folder_name:
        folder_path = Path(folder_name)

        templates = [
            ConfigTemplate("1", "config_one", folder_path.joinpath(Path("config_one.yaml"))),
            ConfigTemplate("2", "config_two", folder_path.joinpath(Path("config_two.yaml"))),
            # Glob returns in alphabetical order
            ConfigTemplate(
                "4",
                "nested/also_nested/config_four",
                folder_path.joinpath(Path("nested/also_nested/config_four.yaml")),
            ),
            ConfigTemplate(
                "3", "nested/config_three", folder_path.joinpath(Path("nested/config_three.yaml"))
            ),
        ]

        _save_config_form_output(json_, "nested/config_three", folder_path)

        actual = _config_form_start_vals("3", templates)

    assert actual == expected
