from playground_bluetooth.cli import scan
from playground_bluetooth.infrastructure import BleakDeviceScanner


def main() -> None:
    scan.main(obj=BleakDeviceScanner)


__all__ = ["main"]
