import sys

import pytest

import playground_bluetooth


def test_main_runs_the_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["playground-bluetooth", "--help"])

    with pytest.raises(SystemExit) as excinfo:
        playground_bluetooth.main()

    assert excinfo.value.code == 0
