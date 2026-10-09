import dataclasses
import json

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from playground_bluetooth.models import BluetoothDevice


def make_ble_device(name: str | None = "Sensor", address: str = "AA:BB:CC:DD:EE:FF") -> BLEDevice:
    return BLEDevice(address, name, None)


def make_adv(local_name: str | None = "Sensor-Local", rssi: int = -60) -> AdvertisementData:
    return AdvertisementData(
        local_name=local_name,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=rssi,
        platform_data=(),
    )


def test_from_bleak_maps_fields() -> None:
    device = BluetoothDevice.from_bleak(make_ble_device(), make_adv())

    assert device == BluetoothDevice(name="Sensor", address="AA:BB:CC:DD:EE:FF", local_name="Sensor-Local", rssi=-60)


def test_from_bleak_keeps_missing_name_as_none() -> None:
    device = BluetoothDevice.from_bleak(make_ble_device(name=None), make_adv(local_name=None))

    assert device.name is None
    assert device.local_name is None


def test_str_is_json() -> None:
    device = BluetoothDevice.from_bleak(make_ble_device(), make_adv())

    assert json.loads(str(device)) == {
        "name": "Sensor",
        "address": "AA:BB:CC:DD:EE:FF",
        "local_name": "Sensor-Local",
        "rssi": -60,
    }


def test_is_frozen() -> None:
    device = BluetoothDevice(name="x", address="y")

    with pytest.raises(dataclasses.FrozenInstanceError):
        device.name = "z"  # type: ignore[misc]
