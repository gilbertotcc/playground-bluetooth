import dataclasses
import json

from bleak import BLEDevice, AdvertisementData


@dataclasses.dataclass(frozen=True)
class BluetoothDevice:
    name: str | None
    address: str
    local_name: str | None = None

    @staticmethod
    def bluetooth_device_from(ble_device: BLEDevice, advertisement_data: AdvertisementData) -> BluetoothDevice:
        return BluetoothDevice(name=ble_device.name,
                               address=ble_device.address,
                               local_name=advertisement_data.local_name)

    def __str__(self) -> str:
        return json.dumps(dataclasses.asdict(self))
