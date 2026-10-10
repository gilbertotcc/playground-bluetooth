from typing import TYPE_CHECKING

import playground_bluetooth
from playground_bluetooth.infrastructure import Scanner
from playground_bluetooth.models import BluetoothDevice


if TYPE_CHECKING:
    import pytest


DEVICES = [
    BluetoothDevice(address="AA:AA:AA:AA:AA:01", name="One", rssi_samples=(-40,)),
    BluetoothDevice(address="AA:AA:AA:AA:AA:02", name="Two", rssi_samples=(-70,)),
]


class FakeScanner(Scanner):
    async def scan(self, timeout: float = 5.0) -> list[BluetoothDevice]:
        return DEVICES


def test_main_prints_one_line_per_device(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(playground_bluetooth, "BleakDeviceScanner", FakeScanner)

    playground_bluetooth.main()

    assert capsys.readouterr().out.splitlines() == [str(d) for d in DEVICES]
