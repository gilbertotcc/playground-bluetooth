import asyncio

from playground_bluetooth.infrastructure import BleakDeviceScanner, Scanner


async def _run(scanner: Scanner) -> None:
    for device in await scanner.scan():
        print(device)


def main() -> None:
    asyncio.run(_run(BleakDeviceScanner()))


__all__ = ["main"]
