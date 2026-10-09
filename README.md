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

## Development

Run these commands from the root of the project to lint, format-check, type
check, and test the code:

```sh
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pytest
```

## Claude Code

This repository is set up for [Claude Code](https://claude.com/claude-code).
Its behavior is configured through `AGENTS.md` and `.claude/settings.json`,
which pre-approves the project's lint, type, and test commands.

GitHub operations use the `gh` CLI, so no environment variables are needed.

## References

* [How to make a simple Bluetooth scanner with Python](https://medium.com/@protobioengineering/tldr-how-to-make-a-simple-bluetooth-scanner-with-python-99023152110e)
* [Bleak – A cross platform Bluetooth Low Energy Client for Python](https://github.com/hbldh/bleak?tab=readme-ov-file)
* [Bluetooth SIG – Assigned Numbers](https://www.bluetooth.com/specifications/assigned-numbers/)

* **bleak / assigned numbers**
  * [Bleak – BleakScanner class](https://bleak.readthedocs.io/en/latest/api/scanner.html)
  * [Bluetooth SIG – Assigned Numbers YAML repository](https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/)
  * [Nordic Semiconductor – Bluetooth Numbers Database](https://github.com/nordicsemi/bluetooth-numbers-database)

* **Address privacy (RPA)**
  * [Silicon Labs – Privacy and Tracking](https://docs.silabs.com/btmesh/9.1.0/bluetooth-application-security-design-considerations/03-privacy-and-tracking)
  * [Ezurio – Why does the BLE MAC address keep changing on my smartphone?](https://www.ezurio.com/support/faqs/why-does-ble-mac-address-keep-changing-my-smartphone)
  * [Cardinal Peak – Bluetooth LE Security and Privacy in Wireless Audio Devices](https://www.cardinalpeak.com/blog/bluetooth-le-security-and-privacy-in-wireless-audio-devices)

* **Device identification / protocols**
  * [Handoff All Your Privacy – A Review of Apple's Bluetooth Low Energy Continuity Protocol (PoPETs 2019)](https://petsymposium.org/popets/2019/popets-2019-0057.php)
  * [Handoff All Your Privacy (arXiv 1904.10600)](https://arxiv.org/abs/1904.10600)
  * [furiousMAC – Apple Continuity protocol dissectors](https://github.com/furiousMAC/continuity)
  * [Adafruit – Use the Cluetooth Scanner](https://learn.adafruit.com/cluetooth-scanner/use-the-cluetooth-scanner)
  * [Google – Eddystone Protocol Specification](https://github.com/google/eddystone/blob/master/protocol-specification.md)
  * [Google – Fast Pair Service](https://developers.google.com/nearby/fast-pair/specifications/introduction)
  * [Microsoft – Swift Pair](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/bluetooth-swift-pair)

* **Tracking despite randomization**
  * [9to5Mac – Bluetooth flaw allows most Apple devices to be tracked](https://9to5mac.com/2019/07/18/bluetooth-flaw/)
  * [Venom: a Visual and Experimental Bluetooth Low Energy Tracking System (WiSec 2020)](https://wisec2020.ins.jku.at/proceedings/wisec20-1.pdf)
  * [Givehchian et al. – Practical Obfuscation of BLE Physical-Layer Fingerprints on Mobile Devices](https://par.nsf.gov/servlets/purl/10587217)
  * [INCIBE – Bluetooth LE devices can be tracked](https://www.incibe.es/index.php/en/incibe-cert/publications/cybersecurity-highlights/bluetooth-le-devices-can-be-tracked)
