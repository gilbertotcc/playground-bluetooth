import enum


class AddressType(enum.Enum):
    """Kind of Bluetooth LE device address (Core Spec Vol 6, Part B, 1.3)."""

    PUBLIC = enum.auto()
    RANDOM_STATIC = enum.auto()
    RESOLVABLE_PRIVATE = enum.auto()
    NON_RESOLVABLE_PRIVATE = enum.auto()
    UNKNOWN = enum.auto()


class DeviceCategory(enum.Enum):
    """Coarse device category inferred from the advertisement."""

    PHONE = enum.auto()
    COMPUTER = enum.auto()
    AUDIO = enum.auto()
    WEARABLE = enum.auto()
    INPUT = enum.auto()
    TRACKER = enum.auto()
    BEACON = enum.auto()
    HEALTH_FITNESS = enum.auto()
    SENSOR = enum.auto()
    MEDIA = enum.auto()
    UNKNOWN = enum.auto()
