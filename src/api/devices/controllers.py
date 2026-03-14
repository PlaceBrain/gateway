from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts.devices_pb2 import (
    CreateActuatorRequest as GrpcCreateActuatorRequest,
)
from placebrain_contracts.devices_pb2 import (
    CreateDeviceRequest as GrpcCreateDeviceRequest,
)
from placebrain_contracts.devices_pb2 import (
    CreateSensorRequest as GrpcCreateSensorRequest,
)
from placebrain_contracts.devices_pb2 import (
    DeleteActuatorRequest as GrpcDeleteActuatorRequest,
)
from placebrain_contracts.devices_pb2 import (
    DeleteDeviceRequest as GrpcDeleteDeviceRequest,
)
from placebrain_contracts.devices_pb2 import (
    DeleteSensorRequest as GrpcDeleteSensorRequest,
)
from placebrain_contracts.devices_pb2 import (
    DeleteThresholdRequest as GrpcDeleteThresholdRequest,
)
from placebrain_contracts.devices_pb2 import (
    GenerateMqttCredentialsRequest as GrpcGenerateMqttCredentialsRequest,
)
from placebrain_contracts.devices_pb2 import (
    GetDeviceRequest as GrpcGetDeviceRequest,
)
from placebrain_contracts.devices_pb2 import (
    ListActuatorsRequest as GrpcListActuatorsRequest,
)
from placebrain_contracts.devices_pb2 import (
    ListDevicesRequest as GrpcListDevicesRequest,
)
from placebrain_contracts.devices_pb2 import (
    ListSensorsRequest as GrpcListSensorsRequest,
)
from placebrain_contracts.devices_pb2 import (
    ListThresholdsRequest as GrpcListThresholdsRequest,
)
from placebrain_contracts.devices_pb2 import (
    RegenerateDeviceTokenRequest as GrpcRegenerateDeviceTokenRequest,
)
from placebrain_contracts.devices_pb2 import (
    SendCommandRequest as GrpcSendCommandRequest,
)
from placebrain_contracts.devices_pb2 import (
    SetThresholdRequest as GrpcSetThresholdRequest,
)
from placebrain_contracts.devices_pb2 import (
    UpdateActuatorRequest as GrpcUpdateActuatorRequest,
)
from placebrain_contracts.devices_pb2 import (
    UpdateDeviceRequest as GrpcUpdateDeviceRequest,
)
from placebrain_contracts.devices_pb2 import (
    UpdateSensorRequest as GrpcUpdateSensorRequest,
)
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.dependencies.auth import AuthenticatedUser

from .schemas import (
    ActuatorListResponse,
    ActuatorResponse,
    CreateActuatorRequest,
    CreateActuatorResponse,
    CreateDeviceRequest,
    CreateDeviceResponse,
    CreateSensorRequest,
    CreateSensorResponse,
    DeviceDetailResponse,
    DeviceListResponse,
    DeviceSummaryResponse,
    MqttCredentialsResponse,
    RegenerateTokenResponse,
    SensorListResponse,
    SensorResponse,
    SetThresholdRequest,
    SetThresholdResponse,
    SuccessResponse,
    ThresholdListResponse,
    ThresholdResponse,
    UpdateActuatorRequest,
    UpdateActuatorResponse,
    UpdateDeviceRequest,
    UpdateDeviceResponse,
    UpdateSensorRequest,
    UpdateSensorResponse,
)
from .schemas import SendCommandRequest as SendCommandBody

router = APIRouter(prefix="/places/{place_id}/devices", tags=["devices"], route_class=DishkaRoute)
mqtt_router = APIRouter(prefix="/mqtt", tags=["mqtt"], route_class=DishkaRoute)

_STATUS_MAP = {0: "unspecified", 1: "online", 2: "offline"}
_VALUE_TYPE_MAP = {0: "unspecified", 1: "number", 2: "boolean", 3: "enum"}
_VALUE_TYPE_REVERSE = {"number": 1, "boolean": 2, "enum": 3}
_THRESHOLD_TYPE_MAP = {0: "unspecified", 1: "min", 2: "max"}
_THRESHOLD_TYPE_REVERSE = {"min": 1, "max": 2}
_SEVERITY_MAP = {0: "unspecified", 1: "warning", 2: "critical"}
_SEVERITY_REVERSE = {"warning": 1, "critical": 2}


# --- Devices ---


@router.post("", response_model=CreateDeviceResponse)
async def create_device(
    place_id: str,
    body: CreateDeviceRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreateDevice(
        GrpcCreateDeviceRequest(user_id=current_user.user_id, place_id=place_id, name=body.name)
    )
    return CreateDeviceResponse(device_id=response.device_id, token=response.token)


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    place_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListDevices(
        GrpcListDevicesRequest(user_id=current_user.user_id, place_id=place_id)
    )
    return DeviceListResponse(
        devices=[
            DeviceSummaryResponse(
                device_id=d.device_id,
                place_id=d.place_id,
                name=d.name,
                status=_STATUS_MAP.get(d.status, "unspecified"),
                last_seen_at=d.last_seen_at,
            )
            for d in response.devices
        ]
    )


@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(
    place_id: str,
    device_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.GetDevice(
        GrpcGetDeviceRequest(user_id=current_user.user_id, place_id=place_id, device_id=device_id)
    )
    d = response.device
    return DeviceDetailResponse(
        device_id=d.device_id,
        place_id=d.place_id,
        name=d.name,
        status=_STATUS_MAP.get(d.status, "unspecified"),
        last_seen_at=d.last_seen_at,
        created_at=d.created_at,
        updated_at=d.updated_at,
        sensors=[
            SensorResponse(
                sensor_id=s.sensor_id,
                device_id=s.device_id,
                key=s.key,
                name=s.name,
                value_type=_VALUE_TYPE_MAP.get(s.value_type, "unspecified"),
                unit_label=s.unit_label,
                precision=s.precision,
            )
            for s in d.sensors
        ],
        actuators=[
            ActuatorResponse(
                actuator_id=a.actuator_id,
                device_id=a.device_id,
                key=a.key,
                name=a.name,
                value_type=_VALUE_TYPE_MAP.get(a.value_type, "unspecified"),
                unit_label=a.unit_label,
                precision=a.precision,
                min_value=a.min_value,
                max_value=a.max_value,
                step=a.step,
                enum_options=list(a.enum_options),
            )
            for a in d.actuators
        ],
    )


@router.put("/{device_id}", response_model=UpdateDeviceResponse)
async def update_device(
    place_id: str,
    device_id: str,
    body: UpdateDeviceRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateDevice(
        GrpcUpdateDeviceRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            name=body.name,
        )
    )
    return UpdateDeviceResponse(device_id=response.device_id)


@router.delete("/{device_id}", response_model=SuccessResponse)
async def delete_device(
    place_id: str,
    device_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteDevice(
        GrpcDeleteDeviceRequest(
            user_id=current_user.user_id, place_id=place_id, device_id=device_id
        )
    )
    return SuccessResponse(success=response.success)


@router.post("/{device_id}/regenerate-token", response_model=RegenerateTokenResponse)
async def regenerate_token(
    place_id: str,
    device_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.RegenerateDeviceToken(
        GrpcRegenerateDeviceTokenRequest(
            user_id=current_user.user_id, place_id=place_id, device_id=device_id
        )
    )
    return RegenerateTokenResponse(token=response.token)


# --- Sensors ---


@router.post("/{device_id}/sensors", response_model=CreateSensorResponse)
async def create_sensor(
    place_id: str,
    device_id: str,
    body: CreateSensorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreateSensor(
        GrpcCreateSensorRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            key=body.key,
            name=body.name,
            value_type=_VALUE_TYPE_REVERSE.get(body.value_type, 1),
            unit_label=body.unit_label,
            precision=body.precision,
        )
    )
    return CreateSensorResponse(sensor_id=response.sensor_id)


@router.get("/{device_id}/sensors", response_model=SensorListResponse)
async def list_sensors(
    place_id: str,
    device_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListSensors(
        GrpcListSensorsRequest(user_id=current_user.user_id, place_id=place_id, device_id=device_id)
    )
    return SensorListResponse(
        sensors=[
            SensorResponse(
                sensor_id=s.sensor_id,
                device_id=s.device_id,
                key=s.key,
                name=s.name,
                value_type=_VALUE_TYPE_MAP.get(s.value_type, "unspecified"),
                unit_label=s.unit_label,
                precision=s.precision,
            )
            for s in response.sensors
        ]
    )


@router.put("/{device_id}/sensors/{sensor_id}", response_model=UpdateSensorResponse)
async def update_sensor(
    place_id: str,
    device_id: str,
    sensor_id: str,
    body: UpdateSensorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateSensor(
        GrpcUpdateSensorRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            sensor_id=sensor_id,
            name=body.name,
            unit_label=body.unit_label,
            precision=body.precision,
        )
    )
    return UpdateSensorResponse(sensor_id=response.sensor_id)


@router.delete("/{device_id}/sensors/{sensor_id}", response_model=SuccessResponse)
async def delete_sensor(
    place_id: str,
    device_id: str,
    sensor_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteSensor(
        GrpcDeleteSensorRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            sensor_id=sensor_id,
        )
    )
    return SuccessResponse(success=response.success)


# --- Thresholds ---


@router.post("/{device_id}/sensors/{sensor_id}/thresholds", response_model=SetThresholdResponse)
async def set_threshold(
    place_id: str,
    device_id: str,
    sensor_id: str,
    body: SetThresholdRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.SetThreshold(
        GrpcSetThresholdRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            sensor_id=sensor_id,
            type=_THRESHOLD_TYPE_REVERSE.get(body.type, 1),
            value=body.value,
            severity=_SEVERITY_REVERSE.get(body.severity, 1),
        )
    )
    return SetThresholdResponse(threshold_id=response.threshold_id)


@router.get("/{device_id}/sensors/{sensor_id}/thresholds", response_model=ThresholdListResponse)
async def list_thresholds(
    place_id: str,
    device_id: str,
    sensor_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListThresholds(
        GrpcListThresholdsRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            sensor_id=sensor_id,
        )
    )
    return ThresholdListResponse(
        thresholds=[
            ThresholdResponse(
                threshold_id=t.threshold_id,
                sensor_id=t.sensor_id,
                type=_THRESHOLD_TYPE_MAP.get(t.type, "unspecified"),
                value=t.value,
                severity=_SEVERITY_MAP.get(t.severity, "unspecified"),
            )
            for t in response.thresholds
        ]
    )


@router.delete(
    "/{device_id}/sensors/{sensor_id}/thresholds/{threshold_id}", response_model=SuccessResponse
)
async def delete_threshold(
    place_id: str,
    device_id: str,
    sensor_id: str,
    threshold_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteThreshold(
        GrpcDeleteThresholdRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            sensor_id=sensor_id,
            threshold_id=threshold_id,
        )
    )
    return SuccessResponse(success=response.success)


# --- Actuators ---


@router.post("/{device_id}/actuators", response_model=CreateActuatorResponse)
async def create_actuator(
    place_id: str,
    device_id: str,
    body: CreateActuatorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreateActuator(
        GrpcCreateActuatorRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            key=body.key,
            name=body.name,
            value_type=_VALUE_TYPE_REVERSE.get(body.value_type, 1),
            unit_label=body.unit_label,
            precision=body.precision,
            min_value=body.min_value or 0,
            max_value=body.max_value or 0,
            step=body.step or 0,
            enum_options=body.enum_options or [],
        )
    )
    return CreateActuatorResponse(actuator_id=response.actuator_id)


@router.get("/{device_id}/actuators", response_model=ActuatorListResponse)
async def list_actuators(
    place_id: str,
    device_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListActuators(
        GrpcListActuatorsRequest(
            user_id=current_user.user_id, place_id=place_id, device_id=device_id
        )
    )
    return ActuatorListResponse(
        actuators=[
            ActuatorResponse(
                actuator_id=a.actuator_id,
                device_id=a.device_id,
                key=a.key,
                name=a.name,
                value_type=_VALUE_TYPE_MAP.get(a.value_type, "unspecified"),
                unit_label=a.unit_label,
                precision=a.precision,
                min_value=a.min_value,
                max_value=a.max_value,
                step=a.step,
                enum_options=list(a.enum_options),
            )
            for a in response.actuators
        ]
    )


@router.put("/{device_id}/actuators/{actuator_id}", response_model=UpdateActuatorResponse)
async def update_actuator(
    place_id: str,
    device_id: str,
    actuator_id: str,
    body: UpdateActuatorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateActuator(
        GrpcUpdateActuatorRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            actuator_id=actuator_id,
            name=body.name,
            unit_label=body.unit_label,
            precision=body.precision,
            min_value=body.min_value or 0,
            max_value=body.max_value or 0,
            step=body.step or 0,
            enum_options=body.enum_options or [],
        )
    )
    return UpdateActuatorResponse(actuator_id=response.actuator_id)


@router.delete("/{device_id}/actuators/{actuator_id}", response_model=SuccessResponse)
async def delete_actuator(
    place_id: str,
    device_id: str,
    actuator_id: str,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteActuator(
        GrpcDeleteActuatorRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            actuator_id=actuator_id,
        )
    )
    return SuccessResponse(success=response.success)


# --- Commands ---


@router.post("/{device_id}/command", response_model=SuccessResponse)
async def send_command(
    place_id: str,
    device_id: str,
    body: SendCommandBody,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.SendCommand(
        GrpcSendCommandRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
            actuator_key=body.actuator_key,
            value=body.value,
        )
    )
    return SuccessResponse(success=response.success)


# --- MQTT credentials ---


@mqtt_router.post("/credentials", response_model=MqttCredentialsResponse)
async def generate_mqtt_credentials(
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.GenerateMqttCredentials(
        GrpcGenerateMqttCredentialsRequest(user_id=current_user.user_id)
    )
    return MqttCredentialsResponse(
        username=response.username,
        password=response.password,
        expires_at=response.expires_at,
    )
