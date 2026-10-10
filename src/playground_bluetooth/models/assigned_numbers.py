"""Lookups in the Bluetooth SIG assigned numbers.

The tables are loaded by the infrastructure layer (see `playground_bluetooth.infrastructure.assigned_numbers`): this
module only holds them and answers queries.
"""

import dataclasses
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


_BASE_UUID_PREFIX = "0000"
_BASE_UUID_SUFFIX = "-0000-1000-8000-00805f9b34fb"


def short_uuid(uuid: str) -> int | None:
    """Return the 16-bit form of a UUID built on the Bluetooth base UUID, or `None`."""
    uuid = uuid.lower()
    if len(uuid) == 36 and uuid.startswith(_BASE_UUID_PREFIX) and uuid.endswith(_BASE_UUID_SUFFIX):
        return int(uuid[4:8], 16)
    return None


@dataclasses.dataclass(frozen=True)
class AssignedNumbers:
    companies: Mapping[int, str]
    """Company identifier -> company name, as used in manufacturer data."""
    uuids: Mapping[int, str]
    """16-bit service or member UUID -> name."""
    appearances: Mapping[int, tuple[str, Mapping[int, str]]]
    """Appearance category -> (category name, subcategory -> subcategory name)."""

    def company_name(self, company_id: int) -> str | None:
        """Return the name of a SIG company identifier."""
        return self.companies.get(company_id)

    def uuid_name(self, uuid: str) -> str | None:
        """Return the name of a SIG service UUID or member UUID."""
        short = short_uuid(uuid)
        return None if short is None else self.uuids.get(short)

    def appearance_name(self, appearance: int) -> str | None:
        """Return the GAP Appearance name, as `"Category"` or `"Category: Subcategory"`."""
        category = self.appearances.get(appearance >> 6)
        if category is None:
            return None
        name, subcategories = category
        subcategory = subcategories.get(appearance & 0x3F)
        return name if subcategory is None else f"{name}: {subcategory}"

    def manufacturer_names(self, company_ids: Iterable[int]) -> tuple[str, ...]:
        """Name each company identifier, falling back to its hex value when unknown."""
        return tuple(self.company_name(cid) or f"0x{cid:04X}" for cid in company_ids)

    def service_names(self, uuids: Iterable[str]) -> tuple[str, ...]:
        """Name each distinct UUID (keeping the order), falling back to the UUID itself when unknown."""
        return tuple(self.uuid_name(uuid) or uuid for uuid in dict.fromkeys(uuids))
