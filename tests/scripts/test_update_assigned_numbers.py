import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from types import ModuleType


SCRIPT = Path(__file__).parents[2] / "scripts/update_assigned_numbers.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("update_assigned_numbers", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = load_script()


def valid_yaml(key: str) -> bytes:
    return f"{key}:\n  - value: 1\n    name: example\n".encode()


def fake_download(url: str) -> bytes:
    for path, key in module.FILES.values():
        if url.endswith(path):
            return valid_yaml(key)
    raise AssertionError(f"unexpected url {url}")


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "download", fake_download)


def snapshot(directory: Path) -> list[str]:
    return sorted(path.name for path in directory.iterdir())


def test_help_shows_examples_and_exit_codes(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COLUMNS", "80")

    with pytest.raises(SystemExit) as exit_info:
        module.main(["--help"])

    output = capsys.readouterr().out
    assert exit_info.value.code == 0
    assert "uv run scripts/update_assigned_numbers.py --check" in output
    assert "uv run scripts/update_assigned_numbers.py --ref <COMMIT>" in output
    for code in ("0", "1", "2", "3", "130"):
        assert any(line.strip().startswith(f"{code} ") for line in output.splitlines())
    assert all(len(line) <= 80 for line in output.splitlines())


def test_short_help_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        module.main(["-h"])

    assert exit_info.value.code == 0
    assert "usage:" in capsys.readouterr().out


def test_download_error_exits_3_and_writes_nothing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def failing(url: str) -> bytes:
        raise OSError("boom")

    monkeypatch.setattr(module, "download", failing)

    code = module.main(["--data-dir", str(tmp_path)])

    assert code == module.EXIT_FETCH_ERROR == 3
    stderr = capsys.readouterr().err
    assert "error:" in stderr
    assert "boom" in stderr
    assert snapshot(tmp_path) == []


def test_invalid_yaml_exits_3(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(module, "download", lambda url: b"key: [unclosed")

    code = module.main(["--data-dir", str(tmp_path)])

    assert code == 3
    assert "error:" in capsys.readouterr().err
    assert snapshot(tmp_path) == []


def test_empty_list_exits_3(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(module, "download", lambda url: b"uuids: []\n")

    assert module.main(["--data-dir", str(tmp_path)]) == 3


def test_check_outdated_exits_1_and_writes_nothing(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    (tmp_path / "service_uuids.yaml").write_bytes(b"old\n")

    code = module.main(["--check", "--data-dir", str(tmp_path)])

    assert code == module.EXIT_OUTDATED == 1
    assert "service_uuids.yaml: outdated" in capsys.readouterr().out
    assert (tmp_path / "service_uuids.yaml").read_bytes() == b"old\n"
    assert snapshot(tmp_path) == ["service_uuids.yaml"]


def test_check_up_to_date_exits_0(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    for name, (_, key) in module.FILES.items():
        (tmp_path / name).write_bytes(valid_yaml(key))

    code = module.main(["--check", "--data-dir", str(tmp_path)])

    assert code == 0
    assert capsys.readouterr().out.count("up to date") == len(module.FILES)


def test_update_writes_files_and_exits_0(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    data_dir = tmp_path / "data"

    code = module.main(["--data-dir", str(data_dir)])

    assert code == 0
    assert snapshot(data_dir) == sorted(module.FILES)
    output = capsys.readouterr().out
    for name, (_, key) in module.FILES.items():
        assert (data_dir / name).read_bytes() == valid_yaml(key)
        assert f"{name}: updated" in output


def test_ref_is_used_in_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    urls: list[str] = []

    def recording(url: str) -> bytes:
        urls.append(url)
        return fake_download(url)

    monkeypatch.setattr(module, "download", recording)

    code = module.main(["--check", "--ref", "abc123", "--data-dir", str(tmp_path)])

    assert code == 1
    assert urls
    assert all("/abc123/" in url for url in urls)


def test_keyboard_interrupt_exits_130(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def interrupt(url: str) -> bytes:
        raise KeyboardInterrupt

    monkeypatch.setattr(module, "download", interrupt)

    code = module.main(["--data-dir", str(tmp_path)])

    assert code == module.EXIT_INTERRUPTED == 130
    assert "Interrupted" in capsys.readouterr().err
    assert snapshot(tmp_path) == []


def test_unknown_option_exits_2() -> None:
    with pytest.raises(SystemExit) as exit_info:
        module.main(["--bogus"])

    assert exit_info.value.code == 2
