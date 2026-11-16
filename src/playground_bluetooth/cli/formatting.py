"""Pure text formatting of devices for the terminal."""

import json
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from playground_bluetooth.models import BluetoothDevice


LINE_WIDTH = 80


def _truncate(text: str, width: int) -> str:
    """Cut `text` to at most `width` characters, ending with an ellipsis when something was removed."""
    if len(text) <= width:
        return text
    if width <= 0:
        return ""
    return f"{text[: width - 1]}…"


def format_line(device: BluetoothDevice, width: int = LINE_WIDTH) -> str:
    """One human-readable line (at most `width` characters): RSSI, category, address and name."""
    rssi = "?" if device.rssi is None else str(device.rssi)
    prefix = f"{rssi:>4} dBm  {device.category.name:<14}  {device.address}  "
    if len(prefix) >= width:
        return _truncate(prefix, width).rstrip()
    name = device.name or device.local_name or ""
    return (prefix + _truncate(name, width - len(prefix))).rstrip()


def format_json(device: BluetoothDevice) -> str:
    """The device as a single-line JSON object."""
    return json.dumps(device.to_dict())
