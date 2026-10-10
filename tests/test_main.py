from typing import TYPE_CHECKING

import playground_bluetooth
from playground_bluetooth.models import BluetoothDevice


if TYPE_CHECKING:
    import pytest


def test_main_prints_one_line_per_device(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    expected = [
        BluetoothDevice(address="AA:AA:AA:AA:AA:01", name="One", rssi_samples=(-40,)),
        BluetoothDevice(address="AA:AA:AA:AA:AA:02", name="Two", rssi_samples=(-70,)),
    ]

    async def fake_scan() -> list[BluetoothDevice]:
        return expected

    monkeypatch.setattr(playground_bluetooth, "scan", fake_scan)

    playground_bluetooth.main()

    assert capsys.readouterr().out.splitlines() == [str(d) for d in expected]
