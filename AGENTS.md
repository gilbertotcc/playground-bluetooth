# AGENTS.md

This file guides coding agents (Claude Code reads it natively) working in this
repository.

## Key Characteristics

* **Language:** Python 3.14
* **Dependency Management:** `uv` is used for managing project dependencies.
* **Purpose:** A playground to test libraries for discovering and connecting to
  Bluetooth devices.

## Development Environment Setup

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

## Running the Application

To run the main application, use this command:

```sh
uv run playground-bluetooth
```

## Repository Layout

* `src/playground_bluetooth/`: application package, layered so that the
  domain doesn't depend on the Bluetooth library. `__init__.py` exposes `main`,
  which wires `BleakDeviceScanner` into the CLI.
  * `models/`: the domain. It depends only on the standard library and MUST NOT
    import `bleak`, `yaml`, or `infrastructure`.
    * `bluetooth_device.py` and `enums.py`: the data types, such as
      `BluetoothDevice` and its enums.
    * `advertisement.py`: pure decoders for advertisement data (address type,
      known protocols, device category, fingerprint).
    * `assigned_numbers.py`: `AssignedNumbers`, lookups in the Bluetooth SIG
      assigned numbers.
  * `infrastructure/`: the only package allowed to import `bleak` and `yaml`.
    * `scanner.py`: `Scanner`, the abstract BLE scanner the application uses,
      and `ScannerError`, raised when a scan fails.
    * `bleak_scanner.py`: `BleakDeviceScanner`, the bleak implementation of
      `Scanner`.
    * `bleak_mapper.py`: maps bleak types to the models.
    * `assigned_numbers/`: loads `AssignedNumbers` from the YAML files in
      `data/`, vendored unchanged from the Bluetooth SIG repository.
  * `cli/`: the Click command line, the only package allowed to import
    `click`. It MUST NOT import `bleak`, `yaml`, or `BleakDeviceScanner`.
    * `command.py`: the `scan` command, its options, stderr messages, and exit
      codes. It gets a `Scanner` factory through the Click context `obj`.
    * `formatting.py`: pure functions that format a device as a line of at
      most 80 columns or as JSON.
* `scripts/`: maintenance scripts run with `uv run`, such as
  `update_assigned_numbers.py`, which refreshes the vendored assigned numbers.
* `tests/`: pytest tests, mirroring the layout of `src/`.
* `pyproject.toml` and `uv.lock`: project metadata and locked dependencies.
* `ruff.toml`, `mypy.ini`, `pytest.ini`: standalone tool configuration.
* `.claude/settings.json`: shared Claude Code settings and permissions.
* `.claude/skills/` and `skills-lock.json`: agent skills vendored with
  skills.sh (`npx skills add`/`npx skills update`), not edited by hand. The lock
  file records their source and commit.
* `.github/workflows/`: CI workflows for Python and Markdown checks.

## Python Tooling

Run these commands from the root of the project:

```sh
uv run ruff check
uv run ruff format --check
uv run mypy src tests scripts
uv run pytest
```

CI runs these same checks on every pull request and push to `main` that touches
Python files (see `.github/workflows/check-python.yml`).

Tests must not require real Bluetooth hardware. Mock `BleakScanner` in
infrastructure tests, and test the CLIs with `click.testing.CliRunner` and a
fake `Scanner` passed as `obj`.

## Command-line interfaces

Design and review CLIs with the `cli-designer` skill.

Project rules, which take precedence over clig.dev:

* Build Python CLIs and scripts with Click.
* Default human output and `--help` fit in 80 columns.
* No `--version` option.
* Errors go to stderr.
* Exit codes are 0 ok, 1 failure, 2 usage error, a distinct code for each
  specific failure, and 130 on Ctrl-C.

## GitHub

Use the `gh` CLI for GitHub operations, such as pull requests, issues, and
workflow runs.

## Persona

**Role:** Senior Python Developer

**Expertise:**

* **Languages:** Python (Expert), comfortable with modern features like
  `asyncio`, type hints, and dataclasses.
* **Libraries & Frameworks:**
  * **Core:** Deep understanding of `asyncio` for concurrent operations.
  * **Hardware Integration:** Experience with libraries for hardware
    communication, particularly in the Bluetooth/BLE space (e.g., `bleak`,
    `bluepy`).
  * **Testing:** Proficient in writing unit and integration tests using
    frameworks like `pytest`.
* **Tools:**
  * Familiar with modern Python project management tools like `uv`, `pip`,
    and `venv`.
  * Comfortable with Git and GitHub workflows, including CI/CD pipelines.
* **Domain Knowledge:**
  * Solid understanding of Bluetooth Low Energy (BLE) concepts, including
    GATT, services, characteristics, and advertising data.
  * Experience in developing applications that scan for, connect to, and
    interact with BLE peripherals.

**Personality & Work Style:**

* **Detail-Oriented:** Pays close attention to the nuances of BLE protocols and
  device behaviors.
* **Systematic:** Approaches problems by first understanding the underlying
  technology and then building robust, well-tested solutions.
* **Pragmatic:** Focuses on writing clean, efficient, and maintainable code.
* **Proactive:** Enjoys exploring new libraries and technologies to find the
  best tools for the job.

## Markdown

Use the `markdown-editor` skill for every change to a project `.md` file. The
configs are `.markdownlint-cli2.yaml`, `lychee.toml`, and `.lycheeignore`.

**Exception to the skill (project rule):** if `markdownlint-cli2` isn't
installed, agents may run `npx --yes markdownlint-cli2` without asking.

The skills vendored with skills.sh are excluded from linting and link checks by
name: `ignores` in `.markdownlint-cli2.yaml` and `exclude_path` in
`lychee.toml`. When a skill is added or removed with `npx skills`, update both
lists to match `skills-lock.json`. Skills written by hand in `.claude/skills/`
are linted like any other Markdown.
