from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.api.enums import DeviceStatus, ThresholdSeverity, ThresholdType, ValueType

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


class SensorResponse(BaseModel):
    sensor_id: UUID
    device_id: UUID
    key: str
    name: str
    value_type: ValueType
    unit_label: str
    precision: int


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


# --- MQTT credentials ---


class MqttCredentialsResponse(BaseModel):
    username: str
    password: str
    expires_at: int
