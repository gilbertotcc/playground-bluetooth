# /// script
# requires-python = ">=3.14"
# dependencies = ["click", "pyyaml"]
# ///
"""Update the vendored Bluetooth SIG assigned numbers.

Examples:
    uv run scripts/update_assigned_numbers.py --check
    uv run scripts/update_assigned_numbers.py
    uv run scripts/update_assigned_numbers.py --ref <COMMIT>

Downloads the YAML files from the Bluetooth SIG repository and rewrites the
vendored copies when they differ. With --check nothing is written. Files are
written only after every download has been fetched and validated.

Exit codes:
    0    up to date, or updated
    1    outdated (with --check)
    2    usage error
    3    fetch or validation failure
    130  interrupted (Ctrl-C)
"""

import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

import click
import yaml


BASE_URL = "https://bitbucket.org/bluetooth-SIG/public/raw/{ref}/assigned_numbers/{path}"
DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parent.parent / "src/playground_bluetooth/infrastructure/assigned_numbers/data"
)
EXIT_OUTDATED = 1
EXIT_FETCH_ERROR = 3
EXIT_INTERRUPTED = 130
TIMEOUT_SECONDS = 30
USER_AGENT = "playground-bluetooth-assigned-numbers-updater"

# Local filename -> (upstream path, expected top-level YAML key)
FILES: dict[str, tuple[str, str]] = {
    "company_identifiers.yaml": ("company_identifiers/company_identifiers.yaml", "company_identifiers"),
    "service_uuids.yaml": ("uuids/service_uuids.yaml", "uuids"),
    "member_uuids.yaml": ("uuids/member_uuids.yaml", "uuids"),
    "appearance_values.yaml": ("core/appearance_values.yaml", "appearance_values"),
}


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310  # https URL only
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310  # https URL only
        data: bytes = response.read()
    return data


def validate(content: bytes, key: str) -> None:
    document: Any = yaml.safe_load(content)
    if not isinstance(document, dict):
        raise ValueError("top-level YAML value is not a mapping")
    entries = document.get(key)
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"missing or empty list under '{key}'")


def fetch_all(ref: str) -> dict[str, bytes]:
    contents: dict[str, bytes] = {}
    for name, (path, key) in FILES.items():
        url = BASE_URL.format(ref=ref, path=path)
        try:
            content = download(url)
            validate(content, key)
        except Exception as error:
            raise RuntimeError(f"{name}: failed to fetch or validate {url}: {error}") from error
        contents[name] = content
    return contents


def is_up_to_date(path: Path, content: bytes) -> bool:
    return path.is_file() and path.read_bytes() == content


def write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(file_descriptor, "wb") as temp_file:
            temp_file.write(content)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


HELP = """Update the vendored Bluetooth SIG assigned numbers.

\b
Examples:
  uv run scripts/update_assigned_numbers.py --check
  uv run scripts/update_assigned_numbers.py
  uv run scripts/update_assigned_numbers.py --ref <COMMIT>

Downloads the YAML files from the Bluetooth SIG repository and rewrites the
vendored copies when they differ. With --check nothing is written.

\b
Exit codes:
  0    up to date, or updated
  1    outdated (with --check)
  2    usage error
  3    fetch or validation failure
  130  interrupted (Ctrl-C)
"""


@click.command(help=HELP, context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 80})
@click.option("--ref", default="main", show_default=True, help="Upstream branch, tag or commit.")
@click.option("--check", is_flag=True, help="Do not write; exit 1 if any file is outdated.")
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=DEFAULT_DATA_DIR,
    show_default=False,
    help="Directory holding the vendored files. [default: the package data dir]",
)
def main(*, ref: str, check: bool, data_dir: Path) -> None:
    try:
        contents = fetch_all(ref)
        outdated = False
        for name, content in contents.items():
            path = data_dir / name
            if is_up_to_date(path, content):
                click.echo(f"{name}: up to date")
            elif check:
                click.echo(f"{name}: outdated")
                outdated = True
            else:
                write_atomically(path, content)
                click.echo(f"{name}: updated")
    except KeyboardInterrupt:
        click.echo("Interrupted", err=True)
        sys.exit(EXIT_INTERRUPTED)
    except RuntimeError as error:
        click.echo(f"error: {error}", err=True)
        sys.exit(EXIT_FETCH_ERROR)
    if outdated:
        sys.exit(EXIT_OUTDATED)


if __name__ == "__main__":
    main()
