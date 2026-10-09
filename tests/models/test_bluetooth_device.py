import dataclasses
import json
from datetime import UTC, datetime
from typing import Any

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from playground_bluetooth.models import AddressType, BluetoothDevice, DeviceCategory


HEART_RATE = "0000180d-0000-1000-8000-00805f9b34fb"


def make_ble_device(name: str | None = "Sensor", address: str = "AA:BB:CC:DD:EE:FF") -> BLEDevice:
    return BLEDevice(address, name, None)


def make_adv(
    local_name: str | None = "Sensor-Local",
    rssi: int = -60,
    manufacturer_data: dict[int, bytes] | None = None,
    service_uuids: list[str] | None = None,
    service_data: dict[str, bytes] | None = None,
    tx_power: int | None = None,
    platform_data: tuple[Any, ...] = (),
) -> AdvertisementData:
    return AdvertisementData(
        local_name=local_name,
        manufacturer_data=manufacturer_data or {},
        service_data=service_data or {},
        service_uuids=service_uuids or [],
        tx_power=tx_power,
        rssi=rssi,
        platform_data=platform_data,
    )


def test_from_bleak_maps_fields() -> None:
    adv = make_adv(manufacturer_data={0x004C: b"\x10\x00"}, service_uuids=[HEART_RATE], tx_power=4)

    device = BluetoothDevice.from_bleak(make_ble_device(), adv)

    assert device == BluetoothDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Sensor",
        local_name="Sensor-Local",
        manufacturer_data={0x004C: b"\x10\x00"},
        service_uuids=(HEART_RATE,),
        tx_power=4,
        rssi_samples=(-60,),
    )


def test_from_bleak_keeps_missing_name_as_none() -> None:
    device = BluetoothDevice.from_bleak(make_ble_device(name=None), make_adv(local_name=None))

    assert device.name is None
    assert device.local_name is None


def test_from_bleak_uses_given_samples_and_drops_unavailable_rssi() -> None:
    seen = datetime(2026, 10, 10, tzinfo=UTC)

    device = BluetoothDevice.from_bleak(
        make_ble_device(), make_adv(), rssi_samples=[-50, 127, -70, -60], first_seen=seen, last_seen=seen
    )

    assert device.rssi_samples == (-50, -70, -60)
    assert device.rssi == -60
    assert device.rssi_median == -60.0
    assert device.first_seen == device.last_seen == seen


def test_from_bleak_reads_bluez_platform_data() -> None:
    props = {"AddressType": "random", "Appearance": 0x00C1}

    device = BluetoothDevice.from_bleak(
        make_ble_device(address="C0:11:22:33:44:55"), make_adv(platform_data=("/org/bluez/hci0/dev_C0", props))
    )

    assert device.platform_address_type == "random"
    assert device.appearance == 0x00C1
    assert device.address_type == AddressType.RANDOM_STATIC
    assert device.appearance_name == "Watch: Sports Watch"
    assert device.category == DeviceCategory.WEARABLE


def test_from_bleak_reads_corebluetooth_platform_data() -> None:
    adv_dict = {"kCBAdvDataIsConnectable": 1}

    device = BluetoothDevice.from_bleak(make_ble_device(), make_adv(platform_data=(object(), adv_dict, -60)))

    assert device.connectable is True
    assert device.address_type == AddressType.UNKNOWN


def test_from_bleak_ignores_unexpected_platform_data() -> None:
    device = BluetoothDevice.from_bleak(make_ble_device(), make_adv(platform_data=(1, 2, 3, 4)))

    assert device.connectable is None
    assert device.platform_address_type is None


def test_identity_uses_stable_address() -> None:
    device = BluetoothDevice(address="00:11:22:33:44:55", platform_address_type="public")

    assert device.is_address_stable
    assert device.identity == "00:11:22:33:44:55"


def test_identity_falls_back_to_fingerprint_for_rotating_addresses() -> None:
    first = BluetoothDevice(address="4A:00:00:00:00:01", platform_address_type="random", local_name="Watch")
    second = BluetoothDevice(address="4B:00:00:00:00:02", platform_address_type="random", local_name="Watch")

    assert not first.is_address_stable
    assert first.identity == second.identity == f"fp:{first.fingerprint}"


def test_classification_properties() -> None:
    device = BluetoothDevice(
        address="AA:BB:CC:DD:EE:FF",
        manufacturer_data={0x004C: bytes.fromhex("1005031c0a0b0c"), 0xFFFF: b""},
        service_uuids=(HEART_RATE,),
    )

    assert device.manufacturers == ("Apple, Inc.", "0xFFFF")
    assert device.services == ("Heart Rate",)
    assert device.protocols == ("Apple Continuity: Nearby Info",)
    assert device.category == DeviceCategory.PHONE


def test_signal_is_unknown_without_samples() -> None:
    device = BluetoothDevice(address="AA:BB:CC:DD:EE:FF")

    assert device.rssi is None
    assert device.rssi_median is None


def test_str_is_json() -> None:
    seen = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    adv = make_adv(manufacturer_data={0x004C: b"\x10\x00"}, service_data={HEART_RATE: b"\x01\x02"})
    device = BluetoothDevice.from_bleak(make_ble_device(), adv, first_seen=seen, last_seen=seen)

    data = json.loads(str(device))

    assert data["address"] == "AA:BB:CC:DD:EE:FF"
    assert data["address_type"] == "UNKNOWN"
    assert data["manufacturers"] == ["Apple, Inc."]
    assert data["manufacturer_data"] == {"0x004C": "1000"}
    assert data["service_data"] == {HEART_RATE: "0102"}
    assert data["rssi_samples"] == 1
    assert data["first_seen"] == "2026-10-10T12:00:00+00:00"


def test_is_frozen_and_hashable() -> None:
    device = BluetoothDevice.from_bleak(make_ble_device(), make_adv(manufacturer_data={0x004C: b"\x10\x00"}))

    with pytest.raises(dataclasses.FrozenInstanceError):
        device.name = "z"  # type: ignore[misc]
    with pytest.raises(TypeError):
        device.manufacturer_data[0x004C] = b""  # type: ignore[index]
    assert hash(device) == hash(dataclasses.replace(device))
