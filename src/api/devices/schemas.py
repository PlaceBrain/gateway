from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from src.core.enums import (
    SEVERITY_FROM_PROTO,
    STATUS_FROM_PROTO,
    THRESHOLD_TYPE_FROM_PROTO,
    VALUE_TYPE_FROM_PROTO,
    DeviceStatus,
    ThresholdSeverity,
    ThresholdType,
    ValueType,
)

# --- Device schemas ---


class CreateDeviceRequest(BaseModel):
    name: str


class CreateDeviceResponse(BaseModel):
    device_id: UUID
    token: str


class DeviceSummaryResponse(BaseModel):
    device_id: UUID
    place_id: UUID
    name: str
    status: DeviceStatus
    last_seen_at: datetime | None

    @classmethod
    def from_proto(cls, d) -> Self:
        return cls(
            device_id=d.device_id,
            place_id=d.place_id,
            name=d.name,
            status=STATUS_FROM_PROTO.get(d.status, "offline"),
            last_seen_at=d.last_seen_at or None,
        )


class SensorResponse(BaseModel):
    sensor_id: UUID
    device_id: UUID
    key: str
    name: str
    value_type: ValueType
    unit_label: str
    precision: int

    @classmethod
    def from_proto(cls, s) -> Self:
        return cls(
            sensor_id=s.sensor_id,
            device_id=s.device_id,
            key=s.key,
            name=s.name,
            value_type=VALUE_TYPE_FROM_PROTO.get(s.value_type, "number"),
            unit_label=s.unit_label,
            precision=s.precision,
        )


class ActuatorResponse(BaseModel):
    actuator_id: UUID
    device_id: UUID
    key: str
    name: str
    value_type: ValueType
    unit_label: str
    precision: int
    min_value: float
    max_value: float
    step: float
    enum_options: list[str]

    @classmethod
    def from_proto(cls, a) -> Self:
        return cls(
            actuator_id=a.actuator_id,
            device_id=a.device_id,
            key=a.key,
            name=a.name,
            value_type=VALUE_TYPE_FROM_PROTO.get(a.value_type, "number"),
            unit_label=a.unit_label,
            precision=a.precision,
            min_value=a.min_value,
            max_value=a.max_value,
            step=a.step,
            enum_options=list(a.enum_options),
        )


class DeviceDetailResponse(BaseModel):
    device_id: UUID
    place_id: UUID
    name: str
    status: DeviceStatus
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime
    sensors: list[SensorResponse]
    actuators: list[ActuatorResponse]


class UpdateDeviceRequest(BaseModel):
    name: str


class UpdateDeviceResponse(BaseModel):
    device_id: UUID


class RegenerateTokenResponse(BaseModel):
    token: str


# --- Sensor schemas ---


class CreateSensorRequest(BaseModel):
    key: str
    name: str
    value_type: ValueType = ValueType.NUMBER
    unit_label: str = ""
    precision: int = 2


class CreateSensorResponse(BaseModel):
    sensor_id: UUID


class UpdateSensorRequest(BaseModel):
    name: str
    unit_label: str = ""
    precision: int = 2


class UpdateSensorResponse(BaseModel):
    sensor_id: UUID


class SensorListResponse(BaseModel):
    sensors: list[SensorResponse]


# --- Threshold schemas ---


class SetThresholdRequest(BaseModel):
    type: ThresholdType
    value: float
    severity: ThresholdSeverity = ThresholdSeverity.WARNING


class SetThresholdResponse(BaseModel):
    threshold_id: UUID


class ThresholdResponse(BaseModel):
    threshold_id: UUID
    sensor_id: UUID
    type: ThresholdType
    value: float
    severity: ThresholdSeverity

    @classmethod
    def from_proto(cls, t) -> Self:
        return cls(
            threshold_id=t.threshold_id,
            sensor_id=t.sensor_id,
            type=THRESHOLD_TYPE_FROM_PROTO.get(t.type, "min"),
            value=t.value,
            severity=SEVERITY_FROM_PROTO.get(t.severity, "warning"),
        )


class ThresholdListResponse(BaseModel):
    thresholds: list[ThresholdResponse]


# --- Actuator schemas ---


class CreateActuatorRequest(BaseModel):
    key: str
    name: str
    value_type: ValueType = ValueType.NUMBER
    unit_label: str = ""
    precision: int = 2
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    enum_options: list[str] | None = None


class CreateActuatorResponse(BaseModel):
    actuator_id: UUID


class UpdateActuatorRequest(BaseModel):
    name: str
    unit_label: str = ""
    precision: int = 2
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    enum_options: list[str] | None = None


class UpdateActuatorResponse(BaseModel):
    actuator_id: UUID


class ActuatorListResponse(BaseModel):
    actuators: list[ActuatorResponse]


# --- Command schemas ---


class SendCommandRequest(BaseModel):
    actuator_key: str
    value: str
