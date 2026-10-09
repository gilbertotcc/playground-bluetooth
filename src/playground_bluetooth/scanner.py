import asyncio
import dataclasses
from datetime import UTC, datetime
from typing import Any

from bleak import BleakScanner
from bleak.args.corebluetooth import CBScannerArgs
from bleak.backends.device import BLEDevice  # noqa: TC002 - bleak calls inspect.signature() on the detection callback
from bleak.backends.scanner import AdvertisementData

from playground_bluetooth.models import BluetoothDevice


@dataclasses.dataclass
class _Observation:
    """Everything received from one address during a scan."""

    device: BLEDevice
    first_seen: datetime
    last_seen: datetime
    local_name: str | None = None
    tx_power: int | None = None
    manufacturer_data: dict[int, bytes] = dataclasses.field(default_factory=dict)
    service_data: dict[str, bytes] = dataclasses.field(default_factory=dict)
    service_uuids: dict[str, None] = dataclasses.field(default_factory=dict)
    platform_data: tuple[Any, ...] = ()
    rssi_samples: list[int] = dataclasses.field(default_factory=list)

    def add(self, device: BLEDevice, adv: AdvertisementData, seen: datetime) -> None:
        # Advertising and scan response packets carry different fields: merge them instead of keeping the last one.
        self.device = device
        self.last_seen = seen
        self.local_name = adv.local_name or self.local_name
        self.tx_power = adv.tx_power if adv.tx_power is not None else self.tx_power
        self.manufacturer_data.update(adv.manufacturer_data)
        self.service_data.update(adv.service_data)
        self.service_uuids.update(dict.fromkeys(adv.service_uuids))
        self.platform_data = adv.platform_data
        self.rssi_samples.append(adv.rssi)

    def to_device(self) -> BluetoothDevice:
        adv = AdvertisementData(
            local_name=self.local_name,
            manufacturer_data=self.manufacturer_data,
            service_data=self.service_data,
            service_uuids=list(self.service_uuids),
            tx_power=self.tx_power,
            rssi=self.rssi_samples[-1],
            platform_data=self.platform_data,
        )
        return BluetoothDevice.from_bleak(
            self.device, adv, rssi_samples=self.rssi_samples, first_seen=self.first_seen, last_seen=self.last_seen
        )


async def scan(timeout: float = 5.0) -> list[BluetoothDevice]:
    """Scan for nearby BLE devices for `timeout` seconds, collecting every advertisement received."""
    observations: dict[str, _Observation] = {}

    def on_advertisement(device: BLEDevice, adv: AdvertisementData) -> None:
        now = datetime.now(UTC)
        observation = observations.setdefault(device.address, _Observation(device, first_seen=now, last_seen=now))
        observation.add(device, adv, now)

    async with BleakScanner(
        detection_callback=on_advertisement,
        # On macOS, use the Bluetooth address instead of the CoreBluetooth UUID (ignored by other backends).
        cb=CBScannerArgs(use_bdaddr=True),
    ):
        await asyncio.sleep(timeout)
    return [observation.to_device() for observation in observations.values()]
