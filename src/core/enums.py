from enum import StrEnum

from placebrain_contracts.collector_pb2 import (
    ALERT_SEVERITY_CRITICAL,
    ALERT_SEVERITY_WARNING,
    ALERT_STATUS_ACTIVE,
    ALERT_STATUS_RESOLVED,
    ALERT_THRESHOLD_TYPE_MAX,
    ALERT_THRESHOLD_TYPE_MIN,
)
from placebrain_contracts.devices_pb2 import (
    DEVICE_STATUS_OFFLINE,
    DEVICE_STATUS_ONLINE,
    THRESHOLD_SEVERITY_CRITICAL,
    THRESHOLD_SEVERITY_WARNING,
    THRESHOLD_TYPE_MAX,
    THRESHOLD_TYPE_MIN,
    VALUE_TYPE_BOOLEAN,
    VALUE_TYPE_ENUM,
    VALUE_TYPE_NUMBER,
)
from placebrain_contracts.places_pb2 import ROLE_ADMIN, ROLE_OWNER, ROLE_VIEWER


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


# Proto int -> StrEnum mappings

ROLE_FROM_PROTO: dict[int, PlaceRole] = {
    ROLE_OWNER: PlaceRole.OWNER,
    ROLE_ADMIN: PlaceRole.ADMIN,
    ROLE_VIEWER: PlaceRole.VIEWER,
}
ROLE_TO_PROTO: dict[PlaceRole, int] = {v: k for k, v in ROLE_FROM_PROTO.items()}

STATUS_FROM_PROTO: dict[int, DeviceStatus] = {
    DEVICE_STATUS_ONLINE: DeviceStatus.ONLINE,
    DEVICE_STATUS_OFFLINE: DeviceStatus.OFFLINE,
}

VALUE_TYPE_FROM_PROTO: dict[int, ValueType] = {
    VALUE_TYPE_NUMBER: ValueType.NUMBER,
    VALUE_TYPE_BOOLEAN: ValueType.BOOLEAN,
    VALUE_TYPE_ENUM: ValueType.ENUM,
}
VALUE_TYPE_TO_PROTO: dict[ValueType, int] = {v: k for k, v in VALUE_TYPE_FROM_PROTO.items()}

THRESHOLD_TYPE_FROM_PROTO: dict[int, ThresholdType] = {
    THRESHOLD_TYPE_MIN: ThresholdType.MIN,
    THRESHOLD_TYPE_MAX: ThresholdType.MAX,
}
THRESHOLD_TYPE_TO_PROTO: dict[ThresholdType, int] = {
    v: k for k, v in THRESHOLD_TYPE_FROM_PROTO.items()
}

SEVERITY_FROM_PROTO: dict[int, ThresholdSeverity] = {
    THRESHOLD_SEVERITY_WARNING: ThresholdSeverity.WARNING,
    THRESHOLD_SEVERITY_CRITICAL: ThresholdSeverity.CRITICAL,
}
SEVERITY_TO_PROTO: dict[ThresholdSeverity, int] = {v: k for k, v in SEVERITY_FROM_PROTO.items()}


class AlertSeverity(StrEnum):
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class AlertThresholdType(StrEnum):
    MIN = "min"
    MAX = "max"


ALERT_SEVERITY_FROM_PROTO: dict[int, AlertSeverity] = {
    ALERT_SEVERITY_WARNING: AlertSeverity.WARNING,
    ALERT_SEVERITY_CRITICAL: AlertSeverity.CRITICAL,
}
ALERT_SEVERITY_TO_PROTO: dict[AlertSeverity, int] = {
    v: k for k, v in ALERT_SEVERITY_FROM_PROTO.items()
}

ALERT_STATUS_FROM_PROTO: dict[int, AlertStatus] = {
    ALERT_STATUS_ACTIVE: AlertStatus.ACTIVE,
    ALERT_STATUS_RESOLVED: AlertStatus.RESOLVED,
}
ALERT_STATUS_TO_PROTO: dict[AlertStatus, int] = {v: k for k, v in ALERT_STATUS_FROM_PROTO.items()}

ALERT_THRESHOLD_TYPE_FROM_PROTO: dict[int, AlertThresholdType] = {
    ALERT_THRESHOLD_TYPE_MIN: AlertThresholdType.MIN,
    ALERT_THRESHOLD_TYPE_MAX: AlertThresholdType.MAX,
}
