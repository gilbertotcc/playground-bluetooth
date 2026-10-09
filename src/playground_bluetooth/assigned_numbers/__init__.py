"""Lookups in the Bluetooth SIG assigned numbers.

The YAML files in `data/` are copied unchanged from
https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/:

* `company_identifiers/company_identifiers.yaml`
* `uuids/service_uuids.yaml`
* `uuids/member_uuids.yaml`
* `core/appearance_values.yaml`
"""

import functools
import importlib.resources
from typing import Any

import yaml


_BASE_UUID_PREFIX = "0000"
_BASE_UUID_SUFFIX = "-0000-1000-8000-00805f9b34fb"


def _load(filename: str) -> Any:
    text = importlib.resources.files(__package__).joinpath("data", filename).read_text(encoding="utf-8")
    return yaml.safe_load(text)


@functools.cache
def _companies() -> dict[int, str]:
    return {entry["value"]: entry["name"] for entry in _load("company_identifiers.yaml")["company_identifiers"]}


@functools.cache
def _uuids() -> dict[int, str]:
    # Members first, so that SIG-defined service names win on (unlikely) collisions.
    names = {entry["uuid"]: entry["name"] for entry in _load("member_uuids.yaml")["uuids"]}
    names.update({entry["uuid"]: entry["name"] for entry in _load("service_uuids.yaml")["uuids"]})
    return names


@functools.cache
def _appearances() -> dict[int, tuple[str, dict[int, str]]]:
    return {
        entry["category"]: (entry["name"], {sub["value"]: sub["name"] for sub in entry.get("subcategory", [])})
        for entry in _load("appearance_values.yaml")["appearance_values"]
    }


def short_uuid(uuid: str) -> int | None:
    """Return the 16-bit form of a UUID built on the Bluetooth base UUID, or `None`."""
    uuid = uuid.lower()
    if len(uuid) == 36 and uuid.startswith(_BASE_UUID_PREFIX) and uuid.endswith(_BASE_UUID_SUFFIX):
        return int(uuid[4:8], 16)
    return None


def company_name(company_id: int) -> str | None:
    """Return the name of a SIG company identifier, as used in manufacturer data."""
    return _companies().get(company_id)


def uuid_name(uuid: str) -> str | None:
    """Return the name of a SIG service UUID or member UUID."""
    short = short_uuid(uuid)
    return None if short is None else _uuids().get(short)


def appearance_name(appearance: int) -> str | None:
    """Return the GAP Appearance name, as `"Category"` or `"Category: Subcategory"`."""
    category = _appearances().get(appearance >> 6)
    if category is None:
        return None
    name, subcategories = category
    subcategory = subcategories.get(appearance & 0x3F)
    return name if subcategory is None else f"{name}: {subcategory}"
