import abc
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from playground_bluetooth.models import BluetoothDevice


class Scanner(abc.ABC):
    """Discovers nearby BLE devices, whatever the Bluetooth library behind it."""

    @abc.abstractmethod
    async def scan(self, timeout: float = 5.0) -> list[BluetoothDevice]:
        """Scan for `timeout` seconds and return every device observed."""
