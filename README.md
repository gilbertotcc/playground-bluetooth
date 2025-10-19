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
uv run python playground-bluetooth/main.py
```

## Gemini CLI

To fully take advantage of Gemini CLI you must set these environment variables.
You can define them in a `.env` file.

* `GITHUB_PAT`: private access token used by the GitHub MCP server.

## References

* <https://medium.com/@protobioengineering/tldr-how-to-make-a-simple-bluetooth-scanner-with-python-99023152110e>
* <https://github.com/hbldh/bleak?tab=readme-ov-file>
* <https://www.bluetooth.com/specifications/assigned-numbers/>
