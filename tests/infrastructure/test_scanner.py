import pytest

from playground_bluetooth.infrastructure import BleakDeviceScanner, Scanner


def test_scanner_is_abstract() -> None:
    with pytest.raises(TypeError):
        Scanner()  # type: ignore[abstract]


def test_bleak_scanner_implements_scanner() -> None:
    assert isinstance(BleakDeviceScanner(), Scanner)
