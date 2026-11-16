import json

from playground_bluetooth.cli.formatting import LINE_WIDTH, _truncate, format_json, format_line
from playground_bluetooth.models import BluetoothDevice


ADDRESS = "AA:BB:CC:DD:EE:FF"


def test_format_line_layout() -> None:
    device = BluetoothDevice(address=ADDRESS, name="Thermo", rssi_samples=(-42,))

    assert format_line(device) == f" -42 dBm  {device.category.name:<14}  {ADDRESS}  Thermo"


def test_format_line_without_rssi_shows_question_mark() -> None:
    line = format_line(BluetoothDevice(address=ADDRESS, name="X"))

    assert line.startswith("   ? dBm  ")


def test_format_line_falls_back_to_local_name_then_empty() -> None:
    assert format_line(BluetoothDevice(address=ADDRESS, local_name="Local")).endswith("  Local")
    assert format_line(BluetoothDevice(address=ADDRESS)).endswith(ADDRESS)


def test_format_line_truncates_long_names() -> None:
    line = format_line(BluetoothDevice(address=ADDRESS, name="n" * 200, rssi_samples=(-1,)))

    assert len(line) == LINE_WIDTH
    assert line.endswith("…")


def test_format_line_truncates_when_prefix_alone_is_too_long() -> None:
    line = format_line(BluetoothDevice(address="A" * 100, name="name"), width=LINE_WIDTH)

    assert len(line) <= LINE_WIDTH


def test_format_line_honors_width() -> None:
    assert len(format_line(BluetoothDevice(address=ADDRESS, name="n" * 50), width=60)) <= 60


def test_truncate() -> None:
    assert _truncate("abc", 3) == "abc"
    assert _truncate("abcd", 3) == "ab…"
    assert _truncate("abcd", 0) == ""


def test_format_json_is_to_dict_dump() -> None:
    device = BluetoothDevice(address=ADDRESS, name="Thermo", rssi_samples=(-42,))

    assert format_json(device) == json.dumps(device.to_dict())
