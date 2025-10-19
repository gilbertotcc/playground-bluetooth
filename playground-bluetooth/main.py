import asyncio

from bleak import BleakScanner, BLEDevice, AdvertisementData

from models.BluetoothDevice import BluetoothDevice


async def main():
    devices: dict[str, tuple[BLEDevice, AdvertisementData]] = await BleakScanner.discover(
        return_adv=True,
        cb={ "use_bdaddr": True } # On macOS, use Bluetooth address instead of UUID
    )
    for device_uuid, ble_device_with_advertisement_data in devices.items():
        bluetooth_device = BluetoothDevice.bluetooth_device_from(ble_device_with_advertisement_data[0],
                                                                 ble_device_with_advertisement_data[1])
        print(bluetooth_device)


if __name__ == "__main__":
    asyncio.run(main())
