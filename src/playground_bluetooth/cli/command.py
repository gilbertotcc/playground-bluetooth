import asyncio
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING

import click

from playground_bluetooth.cli.formatting import format_json, format_line
from playground_bluetooth.infrastructure import Scanner, ScannerError


if TYPE_CHECKING:
    from playground_bluetooth.models import BluetoothDevice


type ScannerFactory = Callable[[], Scanner]

INTERRUPTED_EXIT_CODE = 130


def _signal_order(device: BluetoothDevice) -> tuple[bool, int]:
    return (device.rssi is None, -(device.rssi or 0))


@click.command(
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 80},
    epilog="https://github.com/gilbertotcc/playground-bluetooth",
)
@click.option(
    "-t",
    "--timeout",
    type=click.FloatRange(min=0, min_open=True),
    default=5.0,
    show_default=True,
    metavar="SECONDS",
    help="How long to scan.",
)
@click.option("--json", "as_json", is_flag=True, help="Print one JSON object per device.")
@click.pass_obj
def scan(scanner_factory: ScannerFactory, timeout: float, *, as_json: bool) -> None:
    """Scan for nearby Bluetooth Low Energy devices and list them.

    Without --json, devices are sorted by signal strength, strongest first.
    With --json, one JSON object per line is printed, in discovery order.

    \b
    Examples:
      playground-bluetooth
      playground-bluetooth -t 10
      playground-bluetooth --json | jq .name
    """
    if sys.stderr.isatty():
        click.echo(f"Scanning for {timeout:g} s…", err=True)
    try:
        devices = asyncio.run(scanner_factory().scan(timeout))
    except ScannerError as error:
        click.echo(f"error: {error} (hint: {error.hint})", err=True)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        click.echo("Interrupted", err=True)
        raise SystemExit(INTERRUPTED_EXIT_CODE) from None

    if not devices:
        click.echo("No devices found.", err=True)
        return
    if as_json:
        for device in devices:
            click.echo(format_json(device))
    else:
        # Strongest first; devices without a reading go last.
        for device in sorted(devices, key=_signal_order):
            click.echo(format_line(device))
