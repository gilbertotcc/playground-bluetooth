from playground_bluetooth.models import AssignedNumbers
from playground_bluetooth.models.assigned_numbers import short_uuid


HEART_RATE = "0000180d-0000-1000-8000-00805f9b34fb"
NORDIC_UART = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"

NUMBERS = AssignedNumbers(
    companies={0x004C: "Apple, Inc."},
    uuids={0x180D: "Heart Rate"},
    appearances={0x003: ("Watch", {0x01: "Sports Watch"})},
)


def test_short_uuid() -> None:
    assert short_uuid("0000FEAA-0000-1000-8000-00805F9B34FB") == 0xFEAA
    assert short_uuid(NORDIC_UART) is None


def test_company_name() -> None:
    assert NUMBERS.company_name(0x004C) == "Apple, Inc."
    assert NUMBERS.company_name(0xFFFF) is None


def test_uuid_name() -> None:
    assert NUMBERS.uuid_name(HEART_RATE.upper()) == "Heart Rate"
    assert NUMBERS.uuid_name(NORDIC_UART) is None


def test_appearance_name() -> None:
    assert NUMBERS.appearance_name(0x003 << 6) == "Watch"
    assert NUMBERS.appearance_name((0x003 << 6) | 0x01) == "Watch: Sports Watch"
    assert NUMBERS.appearance_name((0x003 << 6) | 0x3F) == "Watch"
    assert NUMBERS.appearance_name(0x3FF << 6) is None


def test_manufacturer_names_fall_back_to_hex() -> None:
    assert NUMBERS.manufacturer_names([0x004C, 0xFFFF]) == ("Apple, Inc.", "0xFFFF")


def test_service_names_are_distinct_and_fall_back_to_uuid() -> None:
    assert NUMBERS.service_names([HEART_RATE, NORDIC_UART, HEART_RATE]) == ("Heart Rate", NORDIC_UART)
