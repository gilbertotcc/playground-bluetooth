import dataclasses
import json
from typing import TYPE_CHECKING, Self


if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData


@dataclasses.dataclass(frozen=True)
class BluetoothDevice:
    name: str | None
    address: str
    local_name: str | None = None
    rssi: int | None = None

    @classmethod
    def from_bleak(cls, device: BLEDevice, advertisement_data: AdvertisementData) -> Self:
        return cls(
            name=device.name,
            address=device.address,
            local_name=advertisement_data.local_name,
            rssi=advertisement_data.rssi,
        )

    def __str__(self) -> str:
        return json.dumps(dataclasses.asdict(self))
