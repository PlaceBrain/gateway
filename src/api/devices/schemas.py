from pydantic import BaseModel

# --- Device schemas ---


class CreateDeviceRequest(BaseModel):
    name: str


class CreateDeviceResponse(BaseModel):
    device_id: str
    token: str


class DeviceSummaryResponse(BaseModel):
    device_id: str
    place_id: str
    name: str
    status: str
    last_seen_at: str


class DeviceListResponse(BaseModel):
    devices: list[DeviceSummaryResponse]


class SensorResponse(BaseModel):
    sensor_id: str
    device_id: str
    key: str
    name: str
    value_type: str
    unit_label: str
    precision: int


class ActuatorResponse(BaseModel):
    actuator_id: str
    device_id: str
    key: str
    name: str
    value_type: str
    unit_label: str
    precision: int
    min_value: float
    max_value: float
    step: float
    enum_options: list[str]


class DeviceDetailResponse(BaseModel):
    device_id: str
    place_id: str
    name: str
    status: str
    last_seen_at: str
    created_at: str
    updated_at: str
    sensors: list[SensorResponse]
    actuators: list[ActuatorResponse]


class UpdateDeviceRequest(BaseModel):
    name: str


class UpdateDeviceResponse(BaseModel):
    device_id: str


class RegenerateTokenResponse(BaseModel):
    token: str


class SuccessResponse(BaseModel):
    success: bool


class DeleteDeviceResponse(BaseModel):
    success: bool
    warnings: list[str] = []


# --- Sensor schemas ---


class CreateSensorRequest(BaseModel):
    key: str
    name: str
    value_type: str = "number"
    unit_label: str = ""
    precision: int = 2


class CreateSensorResponse(BaseModel):
    sensor_id: str


class SensorListResponse(BaseModel):
    sensors: list[SensorResponse]


class UpdateSensorRequest(BaseModel):
    name: str
    unit_label: str = ""
    precision: int = 2


class UpdateSensorResponse(BaseModel):
    sensor_id: str


# --- Threshold schemas ---


class SetThresholdRequest(BaseModel):
    type: str
    value: float
    severity: str = "warning"


class SetThresholdResponse(BaseModel):
    threshold_id: str


class ThresholdResponse(BaseModel):
    threshold_id: str
    sensor_id: str
    type: str
    value: float
    severity: str


class ThresholdListResponse(BaseModel):
    thresholds: list[ThresholdResponse]


# --- Actuator schemas ---


class CreateActuatorRequest(BaseModel):
    key: str
    name: str
    value_type: str = "number"
    unit_label: str = ""
    precision: int = 2
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    enum_options: list[str] | None = None


class CreateActuatorResponse(BaseModel):
    actuator_id: str


class ActuatorListResponse(BaseModel):
    actuators: list[ActuatorResponse]


class UpdateActuatorRequest(BaseModel):
    name: str
    unit_label: str = ""
    precision: int = 2
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    enum_options: list[str] | None = None


class UpdateActuatorResponse(BaseModel):
    actuator_id: str


# --- Command schemas ---


class SendCommandRequest(BaseModel):
    actuator_key: str
    value: str


# --- MQTT credentials ---


class MqttCredentialsResponse(BaseModel):
    username: str
    password: str
    expires_at: int
