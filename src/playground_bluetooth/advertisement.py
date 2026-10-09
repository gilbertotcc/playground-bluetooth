"""Pure decoders for BLE advertisement data."""

import hashlib
import re
from typing import TYPE_CHECKING

from playground_bluetooth.assigned_numbers import short_uuid
from playground_bluetooth.models.enums import AddressType, DeviceCategory


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping


APPLE = 0x004C
MICROSOFT = 0x0006

EDDYSTONE = 0xFEAA
GOOGLE_FAST_PAIR = 0xFE2C
EXPOSURE_NOTIFICATION = 0xFD6F
TILE = 0xFEED
SAMSUNG_SMARTTAG = 0xFD5A

_MAC_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")

# Apple Continuity message types, see https://github.com/furiousMAC/continuity.
_APPLE_IBEACON = 0x02
_APPLE_CONTINUITY = {
    0x02: "iBeacon",
    0x03: "AirPrint",
    0x05: "AirDrop",
    0x06: "HomeKit",
    0x07: "Proximity Pairing",
    0x08: "Hey Siri",
    0x09: "AirPlay Target",
    0x0A: "AirPlay Source",
    0x0B: "Magic Switch",
    0x0C: "Handoff",
    0x0D: "Tethering Target",
    0x0E: "Tethering Source",
    0x0F: "Nearby Action",
    0x10: "Nearby Info",
    0x12: "Find My",
}

_EDDYSTONE_FRAMES = {0x00: "UID", 0x10: "URL", 0x20: "TLM", 0x30: "EID"}
_EDDYSTONE_UID = 0x00

_SERVICE_PROTOCOLS = {
    GOOGLE_FAST_PAIR: "Google Fast Pair",
    EXPOSURE_NOTIFICATION: "Exposure Notification",
    TILE: "Tile",
    SAMSUNG_SMARTTAG: "Samsung SmartTag",
}

# GAP Appearance categories (the upper 10 bits of the Appearance value).
_APPEARANCE_CATEGORIES = {
    0x001: DeviceCategory.PHONE,
    0x002: DeviceCategory.COMPUTER,
    0x003: DeviceCategory.WEARABLE,
    0x005: DeviceCategory.MEDIA,
    0x006: DeviceCategory.INPUT,
    0x007: DeviceCategory.WEARABLE,
    0x008: DeviceCategory.TRACKER,
    0x009: DeviceCategory.TRACKER,
    0x00A: DeviceCategory.MEDIA,
    0x00B: DeviceCategory.INPUT,
    0x00C: DeviceCategory.HEALTH_FITNESS,
    0x00D: DeviceCategory.HEALTH_FITNESS,
    0x00E: DeviceCategory.HEALTH_FITNESS,
    0x00F: DeviceCategory.INPUT,
    0x010: DeviceCategory.HEALTH_FITNESS,
    0x011: DeviceCategory.HEALTH_FITNESS,
    0x012: DeviceCategory.HEALTH_FITNESS,
    0x015: DeviceCategory.SENSOR,
    0x021: DeviceCategory.AUDIO,
    0x022: DeviceCategory.AUDIO,
    0x025: DeviceCategory.AUDIO,
    0x027: DeviceCategory.MEDIA,
    0x028: DeviceCategory.MEDIA,
    0x029: DeviceCategory.AUDIO,
    0x031: DeviceCategory.HEALTH_FITNESS,
    0x032: DeviceCategory.HEALTH_FITNESS,
    0x034: DeviceCategory.HEALTH_FITNESS,
    0x051: DeviceCategory.HEALTH_FITNESS,
    0x052: DeviceCategory.SENSOR,
}

# Matched by prefix against the decoded protocol names.
_PROTOCOL_CATEGORIES = (
    ("Apple Continuity: Find My", DeviceCategory.TRACKER),
    ("Tile", DeviceCategory.TRACKER),
    ("Samsung SmartTag", DeviceCategory.TRACKER),
    ("iBeacon", DeviceCategory.BEACON),
    ("Eddystone", DeviceCategory.BEACON),
    ("Apple Continuity: Proximity Pairing", DeviceCategory.AUDIO),
    ("Google Fast Pair", DeviceCategory.AUDIO),
    ("Apple Continuity: Nearby Info", DeviceCategory.PHONE),
    ("Apple Continuity: Handoff", DeviceCategory.PHONE),
    ("Microsoft Swift Pair", DeviceCategory.INPUT),
)

_SERVICE_CATEGORIES = {
    0x1809: DeviceCategory.HEALTH_FITNESS,  # Health Thermometer
    0x180D: DeviceCategory.HEALTH_FITNESS,  # Heart Rate
    0x1810: DeviceCategory.HEALTH_FITNESS,  # Blood Pressure
    0x1812: DeviceCategory.INPUT,  # Human Interface Device
    0x1814: DeviceCategory.HEALTH_FITNESS,  # Running Speed and Cadence
    0x1816: DeviceCategory.HEALTH_FITNESS,  # Cycling Speed and Cadence
    0x1818: DeviceCategory.HEALTH_FITNESS,  # Cycling Power
    0x181A: DeviceCategory.SENSOR,  # Environmental Sensing
    0x181D: DeviceCategory.HEALTH_FITNESS,  # Weight Scale
    0x1826: DeviceCategory.HEALTH_FITNESS,  # Fitness Machine
    **dict.fromkeys(range(0x184E, 0x1857), DeviceCategory.AUDIO),  # LE Audio services
}


def classify_address(address: str, platform_address_type: str | None) -> AddressType:
    """Classify an address using the platform's public/random flag and the random sub-type bits.

    Without the platform flag (e.g. on macOS) a public address can't be told apart from a random one,
    so the result is `UNKNOWN` rather than a guess.
    """
    if not _MAC_RE.match(address):
        return AddressType.UNKNOWN
    if platform_address_type == "public":
        return AddressType.PUBLIC
    if platform_address_type != "random":
        return AddressType.UNKNOWN
    match int(address[:2], 16) >> 6:
        case 0b11:
            return AddressType.RANDOM_STATIC
        case 0b01:
            return AddressType.RESOLVABLE_PRIVATE
        case 0b00:
            return AddressType.NON_RESOLVABLE_PRIVATE
        case _:  # 0b10 is reserved
            return AddressType.UNKNOWN


def _short_uuids(uuids: Iterable[str]) -> set[int]:
    return {short for uuid in uuids if (short := short_uuid(uuid)) is not None}


def _service_payload(service_data: Mapping[str, bytes], uuid16: int) -> bytes | None:
    return next((data for uuid, data in service_data.items() if short_uuid(uuid) == uuid16), None)


def _apple_messages(manufacturer_data: Mapping[int, bytes]) -> Iterator[tuple[int, bytes]]:
    """Yield the (type, value) entries of an Apple Continuity payload."""
    payload = manufacturer_data.get(APPLE, b"")
    i = 0
    while i + 2 <= len(payload):
        message_type, length = payload[i], payload[i + 1]
        yield message_type, payload[i + 2 : i + 2 + length]
        i += 2 + length


def _ibeacon(manufacturer_data: Mapping[int, bytes]) -> bytes | None:
    """Return the 21-byte iBeacon body: UUID (16), major (2), minor (2), measured power (1)."""
    return next(
        (value for kind, value in _apple_messages(manufacturer_data) if kind == _APPLE_IBEACON and len(value) == 21),
        None,
    )


def protocols(
    manufacturer_data: Mapping[int, bytes], service_uuids: Iterable[str], service_data: Mapping[str, bytes]
) -> tuple[str, ...]:
    """Name the well-known advertising protocols found in the advertisement."""
    found: list[str] = []
    for kind, _ in _apple_messages(manufacturer_data):
        name = _APPLE_CONTINUITY.get(kind, f"0x{kind:02X}")
        found.append("iBeacon" if kind == _APPLE_IBEACON else f"Apple Continuity: {name}")
    if manufacturer_data.get(MICROSOFT, b"")[:1] == b"\x03":
        found.append("Microsoft Swift Pair")
    eddystone = _service_payload(service_data, EDDYSTONE)
    if eddystone:
        frame = _EDDYSTONE_FRAMES.get(eddystone[0])
        found.append("Eddystone" if frame is None else f"Eddystone-{frame}")
    uuids = _short_uuids(service_uuids) | _short_uuids(service_data)
    found.extend(name for uuid, name in _SERVICE_PROTOCOLS.items() if uuid in uuids)
    return tuple(dict.fromkeys(found))


def infer_category(
    appearance: int | None, protocol_names: Iterable[str], service_uuids: Iterable[str]
) -> DeviceCategory:
    """Infer the device category: Appearance first, then known protocols, then GATT services."""
    if appearance is not None and (category := _APPEARANCE_CATEGORIES.get(appearance >> 6)):
        return category
    names = tuple(protocol_names)
    for prefix, category in _PROTOCOL_CATEGORIES:
        if any(name.startswith(prefix) for name in names):
            return category
    for uuid in sorted(_short_uuids(service_uuids)):
        if category := _SERVICE_CATEGORIES.get(uuid):
            return category
    return DeviceCategory.UNKNOWN


def fingerprint(
    manufacturer_data: Mapping[int, bytes],
    service_uuids: Iterable[str],
    service_data: Mapping[str, bytes],
    local_name: str | None,
    appearance: int | None,
) -> str:
    """Hash the parts of an advertisement that don't change between packets or address rotations.

    Payload bytes are left out (they often carry counters, battery levels or rotating keys), except for the
    identifiers of formats known to be stable: iBeacon UUID/major/minor and Eddystone-UID namespace/instance.
    Identical device models close to each other may share a fingerprint.
    """
    parts = [
        "m=" + ",".join(f"{cid:04x}:{len(data)}" for cid, data in sorted(manufacturer_data.items())),
        "s=" + ",".join(sorted(uuid.lower() for uuid in service_uuids)),
        "d=" + ",".join(sorted(uuid.lower() for uuid in service_data)),
        f"n={local_name or ''}",
        f"a={'' if appearance is None else appearance}",
    ]
    ibeacon = _ibeacon(manufacturer_data)
    if ibeacon is not None:
        parts.append(f"ibeacon={ibeacon[:20].hex()}")
    eddystone = _service_payload(service_data, EDDYSTONE)
    if eddystone and eddystone[0] == _EDDYSTONE_UID and len(eddystone) >= 18:
        parts.append(f"eddystone={eddystone[2:18].hex()}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
