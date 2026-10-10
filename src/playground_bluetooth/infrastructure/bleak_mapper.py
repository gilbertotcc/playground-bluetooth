"""Map what bleak reports to the application models."""

import dataclasses
import types
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self

from playground_bluetooth.models import BluetoothDevice


if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData

    from playground_bluetooth.models import AssignedNumbers


# CoreBluetooth reports 127 when the RSSI is not available.
RSSI_UNAVAILABLE = 127


def normalize_rssi(rssi: int) -> int | None:
    """Return the RSSI in dBm, or `None` when the platform reports it as unavailable."""
    return None if rssi == RSSI_UNAVAILABLE else rssi


@dataclasses.dataclass(frozen=True)
class PlatformFields:
    """The useful fields of bleak's (unstable) platform specific data."""

    appearance: int | None = None
    connectable: bool | None = None
    address_type: str | None = None


def platform_fields(platform_data: tuple[Any, ...]) -> PlatformFields:
    match platform_data:
        case (str(), Mapping() as props):  # BlueZ: (D-Bus object path, device properties)
            return PlatformFields(appearance=props.get("Appearance"), address_type=props.get("AddressType"))
        case (_, Mapping() as adv_data, _):  # CoreBluetooth: (peripheral, advertisement dict, RSSI)
            connectable = adv_data.get("kCBAdvDataIsConnectable")
            return PlatformFields(connectable=None if connectable is None else bool(connectable))
    return PlatformFields()


@dataclasses.dataclass
class Observation:
    """Everything received from one address during a scan."""

    address: str
    name: str | None = None
    local_name: str | None = None
    tx_power: int | None = None
    manufacturer_data: dict[int, bytes] = dataclasses.field(default_factory=dict)
    service_data: dict[str, bytes] = dataclasses.field(default_factory=dict)
    service_uuids: dict[str, None] = dataclasses.field(default_factory=dict)
    platform: PlatformFields = PlatformFields()
    rssi_samples: list[int] = dataclasses.field(default_factory=list)

    @classmethod
    def from_advertisement(cls, device: BLEDevice, adv: AdvertisementData) -> Self:
        observation = cls(device.address)
        observation.add(device, adv)
        return observation

    def add(self, device: BLEDevice, adv: AdvertisementData) -> None:
        # Advertising and scan response packets carry different fields: merge them instead of keeping the last one.
        self.name = device.name or self.name
        self.local_name = adv.local_name or self.local_name
        self.tx_power = adv.tx_power if adv.tx_power is not None else self.tx_power
        self.manufacturer_data.update(adv.manufacturer_data)
        self.service_data.update(adv.service_data)
        self.service_uuids.update(dict.fromkeys(adv.service_uuids))
        platform = platform_fields(adv.platform_data)
        self.platform = PlatformFields(
            appearance=_latest(platform.appearance, self.platform.appearance),
            connectable=_latest(platform.connectable, self.platform.connectable),
            address_type=_latest(platform.address_type, self.platform.address_type),
        )
        rssi = normalize_rssi(adv.rssi)
        if rssi is not None:
            self.rssi_samples.append(rssi)

    def to_device(self, numbers: AssignedNumbers) -> BluetoothDevice:
        appearance = self.platform.appearance
        return BluetoothDevice(
            address=self.address,
            name=self.name,
            local_name=self.local_name,
            manufacturer_data=types.MappingProxyType(dict(self.manufacturer_data)),
            service_uuids=tuple(self.service_uuids),
            service_data=types.MappingProxyType(dict(self.service_data)),
            tx_power=self.tx_power,
            appearance=appearance,
            connectable=self.platform.connectable,
            platform_address_type=self.platform.address_type,
            rssi_samples=tuple(self.rssi_samples),
            manufacturers=numbers.manufacturer_names(self.manufacturer_data),
            services=numbers.service_names((*self.service_uuids, *self.service_data)),
            appearance_name=None if appearance is None else numbers.appearance_name(appearance),
        )


def _latest[T](new: T | None, old: T | None) -> T | None:
    return old if new is None else new
