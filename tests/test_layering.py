"""The domain (`models`) must stay independent of the libraries used by the infrastructure."""

import ast
import pathlib

import pytest

import playground_bluetooth.models


FORBIDDEN = ("bleak", "yaml", "playground_bluetooth.infrastructure")
MODELS = sorted(pathlib.Path(playground_bluetooth.models.__file__).parent.rglob("*.py"))


def imported_modules(path: pathlib.Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("path", MODELS, ids=lambda path: path.name)
def test_models_do_not_import_infrastructure_libraries(path: pathlib.Path) -> None:
    forbidden = {
        module
        for module in imported_modules(path)
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in FORBIDDEN)
    }

    assert not forbidden, f"{path.name} imports {sorted(forbidden)}"
