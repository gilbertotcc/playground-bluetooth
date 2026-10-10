"""Load the Bluetooth SIG assigned numbers from the vendored YAML files.

The YAML files in `data/` are copied unchanged from
https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/ (refresh them with
`uv run scripts/update_assigned_numbers.py`):

* `company_identifiers/company_identifiers.yaml`
* `uuids/service_uuids.yaml`
* `uuids/member_uuids.yaml`
* `core/appearance_values.yaml`
"""

import functools
import importlib.resources
import types
from typing import Any

import yaml

from playground_bluetooth.models import AssignedNumbers


def _load(filename: str) -> Any:
    text = importlib.resources.files(__package__).joinpath("data", filename).read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _companies() -> dict[int, str]:
    return {entry["value"]: entry["name"] for entry in _load("company_identifiers.yaml")["company_identifiers"]}


def _uuids() -> dict[int, str]:
    # Members first, so that SIG-defined service names win on (unlikely) collisions.
    names = {entry["uuid"]: entry["name"] for entry in _load("member_uuids.yaml")["uuids"]}
    names.update({entry["uuid"]: entry["name"] for entry in _load("service_uuids.yaml")["uuids"]})
    return names


def _appearances() -> dict[int, tuple[str, types.MappingProxyType[int, str]]]:
    return {
        entry["category"]: (
            entry["name"],
            types.MappingProxyType({sub["value"]: sub["name"] for sub in entry.get("subcategory", [])}),
        )
        for entry in _load("appearance_values.yaml")["appearance_values"]
    }


@functools.cache
def load_assigned_numbers() -> AssignedNumbers:
    """Load the assigned numbers once and share them."""
    return AssignedNumbers(
        companies=types.MappingProxyType(_companies()),
        uuids=types.MappingProxyType(_uuids()),
        appearances=types.MappingProxyType(_appearances()),
    )


__all__ = ["load_assigned_numbers"]
