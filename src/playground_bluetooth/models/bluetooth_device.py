import dataclasses
import json
import statistics
from typing import TYPE_CHECKING, Any

from playground_bluetooth.models import advertisement
from playground_bluetooth.models.enums import AddressType, DeviceCategory


if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclasses.dataclass(frozen=True)
class BluetoothDevice:
    """A BLE device as observed during a scan.

    Fields hold the raw observation and the Bluetooth SIG names resolved when the device was built; everything
    else decoded from the observation (category, identity...) is exposed as a property.
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
    """Every valid RSSI reading (dBm) received during the scan, in order."""
    manufacturers: tuple[str, ...] = ()
    """Names of the companies in `manufacturer_data`."""
    services: tuple[str, ...] = ()
    """Names of the services in `service_uuids` and `service_data`."""
    appearance_name: str | None = None
    """Name of the `appearance`."""

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
            "manufacturer_data": {f"0x{cid:04X}": data.hex() for cid, data in self.manufacturer_data.items()},
            "service_data": {uuid: data.hex() for uuid, data in self.service_data.items()},
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict())
