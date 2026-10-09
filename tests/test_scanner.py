from typing import Any

import pytest
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

import playground_bluetooth
from playground_bluetooth import scanner
from playground_bluetooth.models import BluetoothDevice


def make_entry(address: str, name: str, rssi: int) -> tuple[BLEDevice, AdvertisementData]:
    adv = AdvertisementData(
        local_name=f"{name}-local",
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=rssi,
        platform_data=(),
    )
    return BLEDevice(address, name, None), adv


EXPECTED = [
    BluetoothDevice(name="One", address="AA:AA:AA:AA:AA:01", local_name="One-local", rssi=-40),
    BluetoothDevice(name="Two", address="AA:AA:AA:AA:AA:02", local_name="Two-local", rssi=-70),
]


@pytest.fixture
def discover_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    async def fake_discover(**kwargs: Any) -> dict[str, tuple[BLEDevice, AdvertisementData]]:
        calls.append(kwargs)
        return {
            "AA:AA:AA:AA:AA:01": make_entry("AA:AA:AA:AA:AA:01", "One", -40),
            "AA:AA:AA:AA:AA:02": make_entry("AA:AA:AA:AA:AA:02", "Two", -70),
        }

    monkeypatch.setattr(BleakScanner, "discover", fake_discover)
    return calls


async def test_scan_returns_converted_devices(discover_calls: list[dict[str, Any]]) -> None:
    devices = await scanner.scan(timeout=2.5)

    assert devices == EXPECTED
    assert discover_calls == [{"timeout": 2.5, "return_adv": True, "cb": {"use_bdaddr": True}}]


def test_main_prints_one_line_per_device(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    async def fake_scan() -> list[BluetoothDevice]:
        return EXPECTED

    monkeypatch.setattr(playground_bluetooth, "scan", fake_scan)

    playground_bluetooth.main()

    assert capsys.readouterr().out.splitlines() == [str(d) for d in EXPECTED]
