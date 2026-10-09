from bleak import BleakScanner
from bleak.args.corebluetooth import CBScannerArgs

from playground_bluetooth.models import BluetoothDevice


async def scan(timeout: float = 5.0) -> list[BluetoothDevice]:
    """Scan for nearby BLE devices for `timeout` seconds."""
    devices = await BleakScanner.discover(
        timeout=timeout,
        return_adv=True,
        # On macOS, use the Bluetooth address instead of the CoreBluetooth UUID (ignored by other backends).
        cb=CBScannerArgs(use_bdaddr=True),
    )
    return [BluetoothDevice.from_bleak(device, adv) for device, adv in devices.values()]
