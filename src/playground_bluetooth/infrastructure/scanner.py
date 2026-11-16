import abc
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from playground_bluetooth.models import BluetoothDevice


class ScannerError(Exception):
    """The scan could not run (Bluetooth off, permission denied...); `hint` suggests what to try."""

    def __init__(self, message: str, hint: str = "check that Bluetooth is on and allowed for this terminal") -> None:
        super().__init__(message)
        self.hint = hint


class Scanner(abc.ABC):
    """Discovers nearby BLE devices, whatever the Bluetooth library behind it."""

    @abc.abstractmethod
    async def scan(self, timeout: float = 5.0) -> list[BluetoothDevice]:
        """Scan for `timeout` seconds and return every device observed.

        Raises `ScannerError` when the scan cannot run.
        """
