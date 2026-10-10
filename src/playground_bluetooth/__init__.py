import asyncio

from playground_bluetooth.infrastructure import scan


async def _run() -> None:
    for device in await scan():
        print(device)


def main() -> None:
    asyncio.run(_run())


__all__ = ["main"]
