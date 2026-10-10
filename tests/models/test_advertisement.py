import pytest

from playground_bluetooth.models import AddressType, DeviceCategory, advertisement


HEART_RATE = "0000180d-0000-1000-8000-00805f9b34fb"
HID = "00001812-0000-1000-8000-00805f9b34fb"
EDDYSTONE = "0000feaa-0000-1000-8000-00805f9b34fb"
FAST_PAIR = "0000fe2c-0000-1000-8000-00805f9b34fb"

IBEACON_UUID = bytes.fromhex("e2c56db5dffb48d2b060d0f5a71096e0")


def ibeacon(minor: int = 2, power: int = 0xC5) -> dict[int, bytes]:
    return {0x004C: bytes([0x02, 0x15]) + IBEACON_UUID + bytes([0x00, 0x01, 0x00, minor, power])}


def eddystone_uid(tx_power_0m: int = 0xEC, instance_last: int = 0x01) -> dict[str, bytes]:
    return {EDDYSTONE: bytes([0x00, tx_power_0m]) + bytes(range(10)) + bytes([0, 0, 0, 0, 0, instance_last])}


@pytest.mark.parametrize(
    ("address", "platform_type", "expected"),
    [
        ("00:11:22:33:44:55", "public", AddressType.PUBLIC),
        ("C0:11:22:33:44:55", "random", AddressType.RANDOM_STATIC),
        ("4A:11:22:33:44:55", "random", AddressType.RESOLVABLE_PRIVATE),
        ("2A:11:22:33:44:55", "random", AddressType.NON_RESOLVABLE_PRIVATE),
        ("8A:11:22:33:44:55", "random", AddressType.UNKNOWN),
        ("C0:11:22:33:44:55", None, AddressType.UNKNOWN),
        ("8F2C5B6E-1234-4D2A-9C4B-0123456789AB", "public", AddressType.UNKNOWN),
    ],
)
def test_classify_address(address: str, platform_type: str | None, expected: AddressType) -> None:
    assert advertisement.classify_address(address, platform_type) == expected


def test_protocols_parses_every_apple_continuity_message() -> None:
    manufacturer_data = {0x004C: bytes.fromhex("1005031c0a0b0c" + "1202aabb")}

    assert advertisement.protocols(manufacturer_data, [], {}) == (
        "Apple Continuity: Nearby Info",
        "Apple Continuity: Find My",
    )


def test_protocols_recognizes_beacons_and_vendor_services() -> None:
    manufacturer_data = {**ibeacon(), 0x0006: bytes([0x03, 0x00])}

    assert advertisement.protocols(manufacturer_data, [FAST_PAIR], eddystone_uid()) == (
        "iBeacon",
        "Microsoft Swift Pair",
        "Eddystone-UID",
        "Google Fast Pair",
    )


def test_protocols_tolerates_truncated_apple_payload() -> None:
    assert advertisement.protocols({0x004C: bytes([0x10])}, [], {}) == ()


def test_infer_category_prefers_appearance() -> None:
    watch = 0x003 << 6

    assert advertisement.infer_category(watch, ["iBeacon"], [HEART_RATE]) == DeviceCategory.WEARABLE


def test_infer_category_falls_back_to_protocols_then_services() -> None:
    assert advertisement.infer_category(None, ["Apple Continuity: Find My"], [HID]) == DeviceCategory.TRACKER
    assert advertisement.infer_category(None, [], [HID]) == DeviceCategory.INPUT
    assert advertisement.infer_category(None, [], []) == DeviceCategory.UNKNOWN


def test_fingerprint_ignores_changing_payload_bytes() -> None:
    first = advertisement.fingerprint({0x004C: bytes.fromhex("10050311")}, [HEART_RATE], {}, "Watch", None)
    second = advertisement.fingerprint({0x004C: bytes.fromhex("10050399")}, [HEART_RATE], {}, "Watch", None)

    assert first == second


def test_fingerprint_changes_with_structure() -> None:
    base = advertisement.fingerprint({0x004C: b"\x10\x00"}, [], {}, "Watch", None)

    assert advertisement.fingerprint({0x004C: b"\x10\x00"}, [], {}, "Other", None) != base
    assert advertisement.fingerprint({0x0006: b"\x10\x00"}, [], {}, "Watch", None) != base
    assert advertisement.fingerprint({0x004C: b"\x10\x00"}, [HID], {}, "Watch", None) != base


def test_fingerprint_keeps_stable_beacon_identifiers() -> None:
    assert advertisement.fingerprint(ibeacon(minor=1), [], {}, None, None) != advertisement.fingerprint(
        ibeacon(minor=2), [], {}, None, None
    )
    assert advertisement.fingerprint(ibeacon(power=0xC5), [], {}, None, None) == advertisement.fingerprint(
        ibeacon(power=0xC0), [], {}, None, None
    )
    assert advertisement.fingerprint({}, [], eddystone_uid(instance_last=1), None, None) != advertisement.fingerprint(
        {}, [], eddystone_uid(instance_last=2), None, None
    )
