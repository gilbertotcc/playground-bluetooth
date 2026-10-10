from typing import Any

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from playground_bluetooth.infrastructure.assigned_numbers import load_assigned_numbers
from playground_bluetooth.infrastructure.bleak_mapper import (
    Observation,
    PlatformFields,
    normalize_rssi,
    platform_fields,
)
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


def to_device(*packets: tuple[BLEDevice, AdvertisementData]) -> BluetoothDevice:
    (device, adv), *others = packets
    observation = Observation.from_advertisement(device, adv)
    for other_device, other_adv in others:
        observation.add(other_device, other_adv)
    return observation.to_device(load_assigned_numbers())


def test_maps_fields_and_resolves_names() -> None:
    adv = make_adv(manufacturer_data={0x004C: b"\x10\x00", 0xFFFF: b""}, service_uuids=[HEART_RATE], tx_power=4)

    device = to_device((make_ble_device(), adv))

    assert device == BluetoothDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Sensor",
        local_name="Sensor-Local",
        manufacturer_data={0x004C: b"\x10\x00", 0xFFFF: b""},
        service_uuids=(HEART_RATE,),
        tx_power=4,
        rssi_samples=(-60,),
        manufacturers=("Apple, Inc.", "0xFFFF"),
        services=("Heart Rate",),
    )


def test_keeps_missing_name_as_none() -> None:
    device = to_device((make_ble_device(name=None), make_adv(local_name=None)))

    assert device.name is None
    assert device.local_name is None


def test_merges_packets_of_the_same_address() -> None:
    ble_device = make_ble_device()

    device = to_device(
        (ble_device, make_adv(rssi=-50, local_name=None, manufacturer_data={0x004C: b"\x10\x00"}, tx_power=4)),
        (ble_device, make_adv(rssi=-70, service_data={HEART_RATE: b"\x01"})),
        (ble_device, make_adv(rssi=-60, local_name=None)),
    )

    assert device.local_name == "Sensor-Local"
    assert device.tx_power == 4
    assert device.manufacturer_data == {0x004C: b"\x10\x00"}
    assert device.service_data == {HEART_RATE: b"\x01"}
    assert device.services == ("Heart Rate",)
    assert device.rssi_samples == (-50, -70, -60)


def test_drops_unavailable_rssi() -> None:
    ble_device = make_ble_device()

    device = to_device((ble_device, make_adv(rssi=-50)), (ble_device, make_adv(rssi=127)))

    assert normalize_rssi(127) is None
    assert device.rssi_samples == (-50,)


def test_reads_bluez_platform_data() -> None:
    props = {"AddressType": "random", "Appearance": 0x00C1}

    device = to_device(
        (make_ble_device(address="C0:11:22:33:44:55"), make_adv(platform_data=("/org/bluez/hci0/dev_C0", props)))
    )

    assert device.platform_address_type == "random"
    assert device.appearance == 0x00C1
    assert device.address_type == AddressType.RANDOM_STATIC
    assert device.appearance_name == "Watch: Sports Watch"
    assert device.category == DeviceCategory.WEARABLE


def test_reads_corebluetooth_platform_data() -> None:
    adv_dict = {"kCBAdvDataIsConnectable": 1}

    device = to_device((make_ble_device(), make_adv(platform_data=(object(), adv_dict, -60))))

    assert device.connectable is True
    assert device.address_type == AddressType.UNKNOWN


def test_keeps_platform_fields_missing_from_later_packets() -> None:
    ble_device = make_ble_device()
    bluez = ("/org/bluez/hci0/dev_AA", {"AddressType": "public", "Appearance": 0x00C1})

    device = to_device((ble_device, make_adv(platform_data=bluez)), (ble_device, make_adv()))

    assert device.platform_address_type == "public"
    assert device.appearance == 0x00C1


@pytest.mark.parametrize("platform_data", [(), (1, 2, 3, 4)])
def test_ignores_unexpected_platform_data(platform_data: tuple[Any, ...]) -> None:
    assert platform_fields(platform_data) == PlatformFields()
