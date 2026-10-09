import dataclasses
import json
import statistics
import types
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, Self

from playground_bluetooth import advertisement, assigned_numbers
from playground_bluetooth.models.enums import AddressType, DeviceCategory


if TYPE_CHECKING:
    from datetime import datetime

    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData


# CoreBluetooth reports 127 when the RSSI is not available.
RSSI_UNAVAILABLE = 127


@dataclasses.dataclass(frozen=True)
class BluetoothDevice:
    """A BLE device as observed during a scan.

    Fields hold the raw observation; everything decoded from it (vendor, category, identity...)
    is exposed as a property.
    """

    address: str
    name: str | None = None
    """Name known to the OS, possibly cached from an earlier connection."""
    local_name: str | None = None
    """Name included in the advertisement."""
    manufacturer_data: Mapping[int, bytes] = dataclasses.field(default_factory=dict, hash=False)
    service_uuids: tuple[str, ...] = ()
    service_data: Mapping[str, bytes] = dataclasses.field(default_factory=dict, hash=False)
    tx_power: int | None = None
    appearance: int | None = None
    """GAP Appearance, only available on BlueZ."""
    connectable: bool | None = None
    platform_address_type: str | None = None
    """`"public"` or `"random"` as reported by BlueZ; unknown on macOS."""
    rssi_samples: tuple[int, ...] = ()
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @classmethod
    def from_bleak(
        cls,
        device: BLEDevice,
        advertisement_data: AdvertisementData,
        *,
        rssi_samples: Iterable[int] | None = None,
        first_seen: datetime | None = None,
        last_seen: datetime | None = None,
    ) -> Self:
        platform = _platform_fields(advertisement_data.platform_data)
        samples = (advertisement_data.rssi,) if rssi_samples is None else rssi_samples
        return cls(
            address=device.address,
            name=device.name,
            local_name=advertisement_data.local_name,
            manufacturer_data=types.MappingProxyType(dict(advertisement_data.manufacturer_data)),
            service_uuids=tuple(advertisement_data.service_uuids),
            service_data=types.MappingProxyType(dict(advertisement_data.service_data)),
            tx_power=advertisement_data.tx_power,
            appearance=platform.get("appearance"),
            connectable=platform.get("connectable"),
            platform_address_type=platform.get("address_type"),
            rssi_samples=tuple(rssi for rssi in samples if rssi != RSSI_UNAVAILABLE),
            first_seen=first_seen,
            last_seen=last_seen,
        )

    # --- Signal ---------------------------------------------------------------------------------------------

    @property
    def rssi(self) -> int | None:
        """Last RSSI reading in dBm."""
        return self.rssi_samples[-1] if self.rssi_samples else None

    @property
    def rssi_median(self) -> float | None:
        return float(statistics.median(self.rssi_samples)) if self.rssi_samples else None

    # --- Identity -------------------------------------------------------------------------------------------

    @property
    def address_type(self) -> AddressType:
        return advertisement.classify_address(self.address, self.platform_address_type)

    @property
    def is_address_stable(self) -> bool:
        """Whether the address survives across scans (it doesn't rotate like private addresses do)."""
        return self.address_type in {AddressType.PUBLIC, AddressType.RANDOM_STATIC}

    @property
    def fingerprint(self) -> str:
        return advertisement.fingerprint(
            self.manufacturer_data, self.service_uuids, self.service_data, self.local_name, self.appearance
        )

    @property
    def identity(self) -> str:
        """Best key to recognize the device across scans: a stable address, else the fingerprint."""
        return self.address if self.is_address_stable else f"fp:{self.fingerprint}"

    # --- Classification -------------------------------------------------------------------------------------

    @property
    def manufacturers(self) -> tuple[str, ...]:
        return tuple(assigned_numbers.company_name(cid) or f"0x{cid:04X}" for cid in self.manufacturer_data)

    @property
    def services(self) -> tuple[str, ...]:
        uuids = dict.fromkeys((*self.service_uuids, *self.service_data))
        return tuple(assigned_numbers.uuid_name(uuid) or uuid for uuid in uuids)

    @property
    def appearance_name(self) -> str | None:
        return None if self.appearance is None else assigned_numbers.appearance_name(self.appearance)

    @property
    def protocols(self) -> tuple[str, ...]:
        return advertisement.protocols(self.manufacturer_data, self.service_uuids, self.service_data)

    @property
    def category(self) -> DeviceCategory:
        return advertisement.infer_category(self.appearance, self.protocols, self.service_uuids)

    # --- Serialization --------------------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "address": self.address,
            "address_type": self.address_type.name,
            "fingerprint": self.fingerprint,
            "name": self.name,
            "local_name": self.local_name,
            "category": self.category.name,
            "manufacturers": list(self.manufacturers),
            "protocols": list(self.protocols),
            "services": list(self.services),
            "appearance": self.appearance,
            "appearance_name": self.appearance_name,
            "connectable": self.connectable,
            "rssi": self.rssi,
            "rssi_median": self.rssi_median,
            "rssi_samples": len(self.rssi_samples),
            "tx_power": self.tx_power,
            "first_seen": None if self.first_seen is None else self.first_seen.isoformat(),
            "last_seen": None if self.last_seen is None else self.last_seen.isoformat(),
            "manufacturer_data": {f"0x{cid:04X}": data.hex() for cid, data in self.manufacturer_data.items()},
            "service_data": {uuid: data.hex() for uuid, data in self.service_data.items()},
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict())


def _platform_fields(platform_data: tuple[Any, ...]) -> dict[str, Any]:
    """Extract the useful fields from bleak's (unstable) platform specific data."""
    fields: dict[str, Any] = {}
    match platform_data:
        case (str(), Mapping() as props):  # BlueZ: (D-Bus object path, device properties)
            fields["address_type"] = props.get("AddressType")
            fields["appearance"] = props.get("Appearance")
        case (_, Mapping() as adv_data, _):  # CoreBluetooth: (peripheral, advertisement dict, RSSI)
            connectable = adv_data.get("kCBAdvDataIsConnectable")
            fields["connectable"] = None if connectable is None else bool(connectable)
    return fields
