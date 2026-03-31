from enum import StrEnum


class PlaceRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class DeviceStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class ValueType(StrEnum):
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"


class ThresholdType(StrEnum):
    MIN = "min"
    MAX = "max"


class ThresholdSeverity(StrEnum):
    WARNING = "warning"
    CRITICAL = "critical"


# Proto int → StrEnum mappings

ROLE_FROM_PROTO: dict[int, PlaceRole] = {
    1: PlaceRole.OWNER,
    2: PlaceRole.ADMIN,
    3: PlaceRole.VIEWER,
}
ROLE_TO_PROTO: dict[PlaceRole, int] = {v: k for k, v in ROLE_FROM_PROTO.items()}

STATUS_FROM_PROTO: dict[int, DeviceStatus] = {
    1: DeviceStatus.ONLINE,
    2: DeviceStatus.OFFLINE,
}

VALUE_TYPE_FROM_PROTO: dict[int, ValueType] = {
    1: ValueType.NUMBER,
    2: ValueType.BOOLEAN,
    3: ValueType.ENUM,
}
VALUE_TYPE_TO_PROTO: dict[ValueType, int] = {v: k for k, v in VALUE_TYPE_FROM_PROTO.items()}

THRESHOLD_TYPE_FROM_PROTO: dict[int, ThresholdType] = {
    1: ThresholdType.MIN,
    2: ThresholdType.MAX,
}
THRESHOLD_TYPE_TO_PROTO: dict[ThresholdType, int] = {
    v: k for k, v in THRESHOLD_TYPE_FROM_PROTO.items()
}

SEVERITY_FROM_PROTO: dict[int, ThresholdSeverity] = {
    1: ThresholdSeverity.WARNING,
    2: ThresholdSeverity.CRITICAL,
}
SEVERITY_TO_PROTO: dict[ThresholdSeverity, int] = {v: k for k, v in SEVERITY_FROM_PROTO.items()}
