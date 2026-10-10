import dataclasses
import json
import types

import pytest

from playground_bluetooth.models import BluetoothDevice, DeviceCategory


HEART_RATE = "0000180d-0000-1000-8000-00805f9b34fb"


def test_signal_uses_the_collected_samples() -> None:
    device = BluetoothDevice(address="AA:BB:CC:DD:EE:FF", rssi_samples=(-50, -70, -60))

    assert device.rssi == -60
    assert device.rssi_median == -60.0


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
        manufacturer_data={0x004C: bytes.fromhex("1005031c0a0b0c")},
        service_uuids=(HEART_RATE,),
    )

    assert device.protocols == ("Apple Continuity: Nearby Info",)
    assert device.category == DeviceCategory.PHONE


def test_signal_is_unknown_without_samples() -> None:
    device = BluetoothDevice(address="AA:BB:CC:DD:EE:FF")

    assert device.rssi is None
    assert device.rssi_median is None


def test_str_is_json() -> None:
    device = BluetoothDevice(
        address="AA:BB:CC:DD:EE:FF",
        manufacturer_data={0x004C: b"\x10\x00"},
        service_data={HEART_RATE: b"\x01\x02"},
        rssi_samples=(-60,),
        manufacturers=("Apple, Inc.",),
        services=("Heart Rate",),
    )

    data = json.loads(str(device))

    assert data["address"] == "AA:BB:CC:DD:EE:FF"
    assert data["address_type"] == "UNKNOWN"
    assert data["manufacturers"] == ["Apple, Inc."]
    assert data["services"] == ["Heart Rate"]
    assert data["manufacturer_data"] == {"0x004C": "1000"}
    assert data["service_data"] == {HEART_RATE: "0102"}
    assert data["rssi_samples"] == 1
    assert "first_seen" not in data


def test_is_frozen_and_hashable() -> None:
    device = BluetoothDevice(
        address="AA:BB:CC:DD:EE:FF", manufacturer_data=types.MappingProxyType({0x004C: b"\x10\x00"})
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        device.name = "z"  # type: ignore[misc]
    with pytest.raises(TypeError):
        device.manufacturer_data[0x004C] = b""  # type: ignore[index]
    assert hash(device) == hash(dataclasses.replace(device))
