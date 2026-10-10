import asyncio
from typing import TYPE_CHECKING

from bleak import BleakScanner
from bleak.args.corebluetooth import CBScannerArgs
from bleak.backends.device import BLEDevice  # noqa: TC002 - bleak calls inspect.signature() on the detection callback
from bleak.backends.scanner import AdvertisementData  # noqa: TC002 - same as above

from playground_bluetooth.infrastructure.assigned_numbers import load_assigned_numbers
from playground_bluetooth.infrastructure.bleak_mapper import Observation


if TYPE_CHECKING:
    from playground_bluetooth.models import BluetoothDevice


async def scan(timeout: float = 5.0) -> list[BluetoothDevice]:
    """Scan for nearby BLE devices for `timeout` seconds, collecting every advertisement received."""
    observations: dict[str, Observation] = {}

    def on_advertisement(device: BLEDevice, adv: AdvertisementData) -> None:
        if (observation := observations.get(device.address)) is None:
            observations[device.address] = Observation.from_advertisement(device, adv)
        else:
            observation.add(device, adv)

    async with BleakScanner(
        detection_callback=on_advertisement,
        # On macOS, use the Bluetooth address instead of the CoreBluetooth UUID (ignored by other backends).
        cb=CBScannerArgs(use_bdaddr=True),
    ):
        await asyncio.sleep(timeout)
    numbers = load_assigned_numbers()
    return [observation.to_device(numbers) for observation in observations.values()]
