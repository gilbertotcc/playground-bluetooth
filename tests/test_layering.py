"""Each layer may only import what the architecture allows (see AGENTS.md)."""

import ast
import pathlib

import pytest

import playground_bluetooth


PACKAGE = pathlib.Path(playground_bluetooth.__file__).parent
FORBIDDEN = {
    "models": ("bleak", "yaml", "click", "playground_bluetooth.infrastructure", "playground_bluetooth.cli"),
    "infrastructure": ("click", "playground_bluetooth.cli"),
    "cli": (
        "bleak",
        "yaml",
        "playground_bluetooth.infrastructure.bleak_scanner",
        "playground_bluetooth.infrastructure.BleakDeviceScanner",
    ),
}
CASES = [
    pytest.param(layer, path, id=str(path.relative_to(PACKAGE)))
    for layer in FORBIDDEN
    for path in sorted((PACKAGE / layer).rglob("*.py"))
]


def imported_modules(path: pathlib.Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
    return modules


@pytest.mark.parametrize(("layer", "path"), CASES)
def test_layer_does_not_import_forbidden_modules(layer: str, path: pathlib.Path) -> None:
    forbidden = {
        module
        for module in imported_modules(path)
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in FORBIDDEN[layer])
    }

    assert not forbidden, f"{path.relative_to(PACKAGE)} imports {sorted(forbidden)}"
