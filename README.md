# Bluetooth playground

Bluetooth playground is a straightforward project designed to test libraries for
discovering and connecting to Bluetooth devices.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) as a package manager to
streamline virtual environment setup, package management, and code development.

To install the required packages, run the following command:

```sh
uv sync
```

To add new dependencies, use the following command:

```sh
uv add <PACKAGE>
```

If a dependency is needed only for development, include the `--dev` argument.

## Run

To run the main application, use this command:

```sh
uv run playground-bluetooth
```

It scans for 5 s and prints one line per device (RSSI, category, address,
name), strongest first. For example:

```sh
uv run playground-bluetooth --help
uv run playground-bluetooth -t 10
uv run playground-bluetooth --json
```

`--json` prints one JSON object per device. The default output used to be these
JSON lines, which are now behind `--json`.

Progress, `No devices found.`, and errors go to stderr. The exit codes are:

* 0: ok.
* 1: the scan failed (for example, Bluetooth is off); a hint is printed.
* 2: usage error.
* 130: interrupted.

## Development

Run these commands from the root of the project to lint, format-check, type
check, and test the code:

```sh
uv run ruff check
uv run ruff format --check
uv run mypy src tests scripts
uv run pytest
```

### Architecture

The code is layered so that the application does not depend on the Bluetooth
library it uses:

* `playground_bluetooth.models` is the domain: the `BluetoothDevice` model and
  the pure decoders of advertisement data. It depends only on the standard
  library.
* `playground_bluetooth.infrastructure` holds everything tied to an external
  library or data source: the abstract `Scanner`, the `ScannerError` it raises,
  its bleak implementation `BleakDeviceScanner`, the mapping of bleak types to
  the models, and the loading of the Bluetooth SIG assigned numbers from YAML.
* `playground_bluetooth.cli` is the Click command line: options, output
  formatting, and exit codes. It uses `Scanner` and `ScannerError`, never bleak.
* `main()` in `playground_bluetooth` is the only place that names
  `BleakDeviceScanner`: it passes it to the command, so tests can pass a fake
  scanner instead.

Ruff bans `bleak` and `yaml` imports outside `infrastructure`, and a test checks
the imports between layers: `models` imports no other layer, and only `cli`
imports `click`.

### Updating the Bluetooth SIG assigned numbers

Company, service UUID, and appearance names come from YAML files copied
unchanged from the [Bluetooth SIG – Assigned Numbers YAML repository](https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/)
into `src/playground_bluetooth/infrastructure/assigned_numbers/data`.

To check whether the vendored files are outdated, without changing them, run:

```sh
uv run scripts/update_assigned_numbers.py --check
```

Every week, the `Update Bluetooth SIG assigned numbers` workflow runs the
script and, if any file changed, runs the tests and opens a pull request with
the update (or refreshes the one already open). It requires *Allow GitHub
Actions to create and approve pull requests* in the repository settings, and CI
does not run automatically on that pull request.

To update the files, run the script without `--check`. Use `--ref` to download
a specific branch, tag, or commit instead of `main`:

```sh
uv run scripts/update_assigned_numbers.py
uv run scripts/update_assigned_numbers.py --ref <COMMIT>
```

The script validates every download before writing, and writes nothing if any
download fails. Run the script with `--help` for all options. Its exit codes
are:

* 0: up to date, or updated.
* 1: outdated (with `--check`).
* 2: usage error.
* 3: a download or the validation failed; nothing is written.
* 130: interrupted.

Review the changes with `git diff`, run `uv run pytest`, and
commit the updated files.

## Claude Code

This repository is set up for [Claude Code](https://claude.com/claude-code).
Its behavior is configured through `AGENTS.md` and `.claude/settings.json`,
which pre-approves the project's lint, type, and test commands.

The `.claude/skills/` directory holds the `markdown-editor` and `cli-designer`
skills from [gilbertotcc/agent-skills](https://github.com/gilbertotcc/agent-skills),
installed with [skills.sh](https://skills.sh/) and pinned in `skills-lock.json`.

GitHub operations use the `gh` CLI, so no environment variables are needed.

## References

* [Bleak – A cross platform Bluetooth Low Energy Client for Python](https://github.com/hbldh/bleak/tree/v3.1.0):
  the library, at the locked version.
* [Bluetooth SIG – Assigned Numbers](https://www.bluetooth.com/specifications/assigned-numbers/):
  the official assigned numbers.
* [How to make a simple Bluetooth scanner with Python](https://medium.com/@protobioengineering/tldr-how-to-make-a-simple-bluetooth-scanner-with-python-99023152110e):
  the tutorial this project started from.

### bleak and assigned numbers

* [Bleak – BleakScanner class](https://bleak.readthedocs.io/en/latest/api/scanner.html):
  the scanner API.
* [Bluetooth SIG – Assigned Numbers YAML repository](https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/):
  the YAML files vendored by this project.
* [Nordic Semiconductor – Bluetooth Numbers Database](https://github.com/nordicsemi/bluetooth-numbers-database/tree/5c795f597125b7be0d5033fb648e9b6f5e09d9c9):
  community-maintained company and service names.

### Address privacy (RPA)

* [Cardinal Peak – Bluetooth LE Security and Privacy in Wireless Audio Devices](https://www.cardinalpeak.com/blog/bluetooth-le-security-and-privacy-in-wireless-audio-devices):
  address randomization in audio devices.
* [Ezurio – Why does the BLE MAC address keep changing on my smartphone?](https://www.ezurio.com/support/faqs/why-does-ble-mac-address-keep-changing-my-smartphone):
  why phone addresses rotate.
* [Silicon Labs – Privacy and Tracking](https://docs.silabs.com/btmesh/9.1.0/bluetooth-application-security-design-considerations/03-privacy-and-tracking):
  resolvable private addresses and tracking.

### Device identification and protocols

* [Adafruit – Use the Cluetooth Scanner](https://learn.adafruit.com/cluetooth-scanner/use-the-cluetooth-scanner):
  recognizing devices from their advertisements.
* [furiousMAC – Apple Continuity protocol dissectors](https://github.com/furiousMAC/continuity/tree/d9fa98bddafbfa3baafc84e37a417d78a0598546):
  reverse-engineered Continuity message formats.
* [Google – Eddystone Protocol Specification](https://github.com/google/eddystone/blob/bb8738d7ddac0ddd3dfa70e594d011a0475e763d/protocol-specification.md):
  the Eddystone beacon frames.
* [Google – Fast Pair Service](https://developers.google.com/nearby/fast-pair/specifications/introduction):
  the Fast Pair advertisement.
* [Martin et al., 2019] Martin, J., Alpuche, D., Bodeman, K., Brown, L.,
  Fenske, E., Foppe, L., Mayberry, T., Rye, E., Sipes, B., & Teplov, S.
  (2019). Handoff all your privacy: A review of Apple's Bluetooth Low Energy
  Continuity protocol.
  *Proceedings on Privacy Enhancing Technologies, 2019*(4), 34-53. Also
  available as [arXiv:1904.10600](https://arxiv.org/abs/1904.10600).
* [Microsoft – Swift Pair](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/bluetooth-swift-pair):
  the Swift Pair advertisement.

### Tracking despite randomization

* [9to5Mac – Bluetooth flaw allows most Apple devices to be tracked](https://9to5mac.com/2019/07/18/bluetooth-flaw/):
  news coverage of the tracking flaw.
* [Celosia & Cunche, 2020] Celosia, G., & Cunche, M. (2020).
  *Venom: A visual and experimental Bluetooth Low Energy tracking system*
  [Paper presentation]. 13th ACM Conference on Security and Privacy in
  Wireless and Mobile Networks (WiSec 2020), Linz, Austria.
* [Givehchian et al., 2024] Givehchian, H., Bhaskar, N., Redding, A., Zhao, H.,
  Schulman, A., & Bharadia, D. (2024). Practical obfuscation of BLE
  physical-layer fingerprints on mobile devices. In
  *2024 IEEE Symposium on Security and Privacy (SP)* (pp. 2867-2885). IEEE.
* [INCIBE – Bluetooth LE devices can be tracked](https://www.incibe.es/index.php/en/incibe-cert/publications/cybersecurity-highlights/bluetooth-le-devices-can-be-tracked):
  advisory on tracking BLE devices.

[Celosia & Cunche, 2020]: https://wisec2020.ins.jku.at/proceedings/wisec20-1.pdf
[Givehchian et al., 2024]: https://doi.org/10.1109/SP54263.2024.00073
[Martin et al., 2019]: https://doi.org/10.2478/popets-2019-0057
