import inspect
from typing import TYPE_CHECKING, Any, ClassVar, Self

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from playground_bluetooth.infrastructure import bleak_scanner


if TYPE_CHECKING:
    from collections.abc import Callable


HEART_RATE = "0000180d-0000-1000-8000-00805f9b34fb"


def make_adv(
    rssi: int,
    local_name: str | None = None,
    manufacturer_data: dict[int, bytes] | None = None,
    service_uuids: list[str] | None = None,
    tx_power: int | None = None,
) -> AdvertisementData:
    return AdvertisementData(
        local_name=local_name,
        manufacturer_data=manufacturer_data or {},
        service_data={},
        service_uuids=service_uuids or [],
        tx_power=tx_power,
        rssi=rssi,
        platform_data=(),
    )


ONE = BLEDevice("AA:AA:AA:AA:AA:01", "One", None)
TWO = BLEDevice("AA:AA:AA:AA:AA:02", "Two", None)

# Advertising and scan response packets of the same device carry different fields.
ADVERTISEMENTS = [
    (ONE, make_adv(-40, manufacturer_data={0x004C: b"\x10\x00"}, tx_power=4)),
    (TWO, make_adv(-70, local_name="Two-local")),
    (ONE, make_adv(-50, local_name="One-local", service_uuids=[HEART_RATE])),
    (ONE, make_adv(-45)),
]


class FakeBleakScanner:
    instances: ClassVar[list[FakeBleakScanner]] = []

    def __init__(self, detection_callback: Callable[[BLEDevice, AdvertisementData], None], **kwargs: Any) -> None:
        # Like bleak, which evaluates the callback annotations: they must be importable at runtime.
        assert len(inspect.signature(detection_callback).parameters) == 2
        self.detection_callback = detection_callback
        self.kwargs = kwargs
        FakeBleakScanner.instances.append(self)

    async def __aenter__(self) -> Self:
        for device, adv in ADVERTISEMENTS:
            self.detection_callback(device, adv)
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


@pytest.fixture
def fake_scanner(monkeypatch: pytest.MonkeyPatch) -> type[FakeBleakScanner]:
    FakeBleakScanner.instances = []
    monkeypatch.setattr(bleak_scanner, "BleakScanner", FakeBleakScanner)
    return FakeBleakScanner


async def test_scan_aggregates_advertisements_per_device(fake_scanner: type[FakeBleakScanner]) -> None:
    devices = {device.address: device for device in await bleak_scanner.scan(timeout=0)}

    one = devices["AA:AA:AA:AA:AA:01"]
    assert one.name == "One"
    assert one.local_name == "One-local"
    assert one.rssi_samples == (-40, -50, -45)
    assert one.rssi_median == -45.0
    assert one.manufacturer_data == {0x004C: b"\x10\x00"}
    assert one.service_uuids == (HEART_RATE,)
    assert one.tx_power == 4
    assert one.manufacturers == ("Apple, Inc.",)
    assert one.services == ("Heart Rate",)

    two = devices["AA:AA:AA:AA:AA:02"]
    assert two.rssi_samples == (-70,)
    assert two.local_name == "Two-local"


async def test_scan_uses_bdaddr_on_macos(fake_scanner: type[FakeBleakScanner]) -> None:
    await bleak_scanner.scan(timeout=0)

    assert [instance.kwargs for instance in fake_scanner.instances] == [{"cb": {"use_bdaddr": True}}]
