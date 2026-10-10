import pytest

from playground_bluetooth.infrastructure.assigned_numbers import load_assigned_numbers


def test_loads_company_names() -> None:
    numbers = load_assigned_numbers()

    assert numbers.company_name(0x004C) == "Apple, Inc."
    assert numbers.company_name(0xFFFF) is None


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
def test_loads_service_and_member_uuids(uuid: str, expected: str | None) -> None:
    assert load_assigned_numbers().uuid_name(uuid) == expected


def test_loads_appearance_values() -> None:
    numbers = load_assigned_numbers()

    assert numbers.appearance_name(0x003 << 6) == "Watch"
    assert numbers.appearance_name((0x003 << 6) | 0x01) == "Watch: Sports Watch"
    assert numbers.appearance_name(0x3FF << 6) is None


def test_is_loaded_once_and_read_only() -> None:
    numbers = load_assigned_numbers()

    assert load_assigned_numbers() is numbers
    with pytest.raises(TypeError):
        numbers.companies[0xFFFF] = "Nobody"  # type: ignore[index]
