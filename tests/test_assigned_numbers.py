import pytest

from playground_bluetooth import assigned_numbers


def test_company_name() -> None:
    assert assigned_numbers.company_name(0x004C) == "Apple, Inc."
    assert assigned_numbers.company_name(0xFFFF) is None


@pytest.mark.parametrize(
    ("uuid", "expected"),
    [
        ("0000180d-0000-1000-8000-00805f9b34fb", "Heart Rate"),
        ("0000180D-0000-1000-8000-00805F9B34FB", "Heart Rate"),
        ("0000fe2c-0000-1000-8000-00805f9b34fb", "Google LLC"),
        ("0000ffff-0000-1000-8000-00805f9b34fb", None),
        ("6e400001-b5a3-f393-e0a9-e50e24dcca9e", None),
    ],
)
def test_uuid_name(uuid: str, expected: str | None) -> None:
    assert assigned_numbers.uuid_name(uuid) == expected


def test_short_uuid() -> None:
    assert assigned_numbers.short_uuid("0000feaa-0000-1000-8000-00805f9b34fb") == 0xFEAA
    assert assigned_numbers.short_uuid("6e400001-b5a3-f393-e0a9-e50e24dcca9e") is None


def test_appearance_name() -> None:
    assert assigned_numbers.appearance_name(0x003 << 6) == "Watch"
    assert assigned_numbers.appearance_name((0x003 << 6) | 0x01) == "Watch: Sports Watch"
    assert assigned_numbers.appearance_name((0x003 << 6) | 0x3F) == "Watch"
    assert assigned_numbers.appearance_name(0x3FF << 6) is None
