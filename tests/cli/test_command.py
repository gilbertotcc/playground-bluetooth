import json

from click.testing import CliRunner, Result

from playground_bluetooth.cli import scan
from playground_bluetooth.cli.formatting import LINE_WIDTH, format_json
from playground_bluetooth.infrastructure import Scanner, ScannerError
from playground_bluetooth.models import BluetoothDevice


DEVICES = [
    BluetoothDevice(address="AA:AA:AA:AA:AA:01", name="Weak", rssi_samples=(-80,)),
    BluetoothDevice(address="AA:AA:AA:AA:AA:02", name="Unknown"),
    BluetoothDevice(address="AA:AA:AA:AA:AA:03", name="n" * 200, rssi_samples=(-30,)),
    BluetoothDevice(address="AA:AA:AA:AA:AA:04", name="Mid", rssi_samples=(-50,)),
]


class FakeScanner(Scanner):
    def __init__(self, devices: list[BluetoothDevice] | None = None, error: BaseException | None = None) -> None:
        self.devices = devices or []
        self.error = error
        self.timeouts: list[float] = []

    async def scan(self, timeout: float = 5.0) -> list[BluetoothDevice]:
        self.timeouts.append(timeout)
        if self.error is not None:
            raise self.error
        return self.devices


def invoke(scanner: FakeScanner, *args: str, calls: list[int] | None = None) -> Result:
    def factory() -> FakeScanner:
        if calls is not None:
            calls.append(1)
        return scanner

    return CliRunner().invoke(scan, args, obj=factory)


def test_default_output_is_sorted_by_rssi_and_fits_the_line() -> None:
    result = invoke(FakeScanner(DEVICES))

    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert [line.split()[3] for line in lines] == [f"AA:AA:AA:AA:AA:0{n}" for n in (3, 4, 1, 2)]
    assert all(len(line) <= LINE_WIDTH for line in lines)


def test_json_output_keeps_scan_order() -> None:
    result = invoke(FakeScanner(DEVICES), "--json")

    assert result.exit_code == 0
    assert result.stdout.splitlines() == [json.dumps(d.to_dict()) for d in DEVICES]
    assert result.stdout.splitlines()[0] == format_json(DEVICES[0])


def test_help_does_not_scan_and_fits_80_columns() -> None:
    for flag in ("--help", "-h"):
        calls: list[int] = []
        result = invoke(FakeScanner(), flag, calls=calls)

        assert result.exit_code == 0
        assert not calls
        assert "playground-bluetooth --json | jq .name" in result.stdout
        assert all(len(line) <= 80 for line in result.stdout.splitlines())


def test_scanner_error_exits_1_with_hint() -> None:
    result = invoke(FakeScanner(error=ScannerError("off", hint="turn it on")))

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "error: off (hint: turn it on)" in result.stderr


def test_keyboard_interrupt_exits_130() -> None:
    result = invoke(FakeScanner(error=KeyboardInterrupt()))

    assert result.exit_code == 130
    assert result.stdout == ""
    assert "Interrupted" in result.stderr
    assert "Aborted" not in result.stderr


def test_no_devices_exits_0_with_message_on_stderr() -> None:
    result = invoke(FakeScanner([]))

    assert result.exit_code == 0
    assert result.stdout == ""
    assert "No devices found." in result.stderr


def test_timeout_is_passed_through() -> None:
    scanner = FakeScanner()

    invoke(scanner, "-t", "2.5")

    assert scanner.timeouts == [2.5]


def test_default_timeout_is_5_seconds() -> None:
    scanner = FakeScanner()

    invoke(scanner)

    assert scanner.timeouts == [5.0]


def test_zero_timeout_is_a_usage_error() -> None:
    result = invoke(FakeScanner(), "--timeout", "0")

    assert result.exit_code == 2
