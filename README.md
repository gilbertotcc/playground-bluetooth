# Bluetooth playground

Bluetooth playground is a straightforward project designed to test libraries for
discovering and connecting to Bluetooth devices.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) as a package manager; install
it to work on the code.

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
