import pytest

from playground_bluetooth.infrastructure import BleakDeviceScanner, Scanner, ScannerError


def test_scanner_is_abstract() -> None:
    with pytest.raises(TypeError):
        Scanner()  # type: ignore[abstract]


def test_bleak_scanner_implements_scanner() -> None:
    assert isinstance(BleakDeviceScanner(), Scanner)


def test_scanner_error_has_default_hint() -> None:
    error = ScannerError("boom")

    assert str(error) == "boom"
    assert error.hint == "check that Bluetooth is on and allowed for this terminal"


def test_scanner_error_accepts_custom_hint() -> None:
    assert ScannerError("boom", hint="try again").hint == "try again"
