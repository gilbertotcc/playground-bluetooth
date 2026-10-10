# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""Update the vendored Bluetooth SIG assigned numbers.

Usage: uv run scripts/update_assigned_numbers.py [--ref main] [--check]

Downloads the YAML files from the Bluetooth SIG repository and rewrites the
vendored copies when they differ. With --check nothing is written and the exit
code is 1 if any file is outdated.
"""

import argparse
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

import yaml


BASE_URL = "https://bitbucket.org/bluetooth-SIG/public/raw/{ref}/assigned_numbers/{path}"
DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parent.parent / "src/playground_bluetooth/infrastructure/assigned_numbers/data"
)
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


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--ref", default="main", help="upstream branch, tag or commit (default: main)")
    parser.add_argument("--check", action="store_true", help="do not write; exit 1 if any file is outdated")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="directory holding the vendored files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        contents = fetch_all(args.ref)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    outdated = False
    for name, content in contents.items():
        path = args.data_dir / name
        if is_up_to_date(path, content):
            print(f"{name}: up to date")
        elif args.check:
            print(f"{name}: outdated")
            outdated = True
        else:
            write_atomically(path, content)
            print(f"{name}: updated")
    return 1 if outdated else 0


if __name__ == "__main__":
    raise SystemExit(main())
