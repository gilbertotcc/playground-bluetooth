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

* <https://medium.com/@protobioengineering/tldr-how-to-make-a-simple-bluetooth-scanner-with-python-99023152110e>
* <https://github.com/hbldh/bleak?tab=readme-ov-file>
* <https://www.bluetooth.com/specifications/assigned-numbers/>
