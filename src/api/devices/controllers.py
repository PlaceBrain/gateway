import logging
from uuid import UUID

import grpc
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts.collector_pb2 import DeleteReadingsRequest
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
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

from src.api.enums import (
    SEVERITY_FROM_PROTO,
    SEVERITY_TO_PROTO,
    STATUS_FROM_PROTO,
    THRESHOLD_TYPE_FROM_PROTO,
    THRESHOLD_TYPE_TO_PROTO,
    VALUE_TYPE_FROM_PROTO,
    VALUE_TYPE_TO_PROTO,
)
from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import (
    AUTH_ERRORS,
    CONFLICT_ERRORS,
    FORBIDDEN_ERRORS,
    NOT_FOUND_ERRORS,
    DeleteResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
)

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
    DeviceSummaryResponse,
    MqttCredentialsResponse,
    RegenerateTokenResponse,
    SensorListResponse,
    SensorResponse,
    SetThresholdRequest,
    SetThresholdResponse,
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places/{place_id}/devices", tags=["devices"], route_class=DishkaRoute)
mqtt_router = APIRouter(prefix="/mqtt", tags=["mqtt"], route_class=DishkaRoute)


# --- Devices ---


@router.post(
    "",
    status_code=201,
    response_model=CreateDeviceResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **CONFLICT_ERRORS},
)
async def create_device(
    place_id: UUID,
    body: CreateDeviceRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreateDevice(
        GrpcCreateDeviceRequest(
            user_id=current_user.user_id, place_id=str(place_id), name=body.name
        )
    )
    return CreateDeviceResponse(device_id=response.device_id, token=response.token)


@router.get(
    "",
    response_model=PaginatedResponse[DeviceSummaryResponse],
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS},
)
async def list_devices(
    place_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
    pagination: PaginationParams,
):
    response = await stub.ListDevices(
        GrpcListDevicesRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            page=pagination.page,
            per_page=pagination.per_page,
        )
    )
    return PaginatedResponse(
        items=[
            DeviceSummaryResponse(
                device_id=d.device_id,
                place_id=d.place_id,
                name=d.name,
                status=STATUS_FROM_PROTO.get(d.status, "offline"),
                last_seen_at=d.last_seen_at or None,
            )
            for d in response.devices
        ],
        total=response.total,
        page=pagination.page,
        per_page=pagination.per_page,
        has_next=(pagination.page * pagination.per_page) < response.total,
        has_prev=pagination.page > 1,
    )


@router.get(
    "/{device_id}",
    response_model=DeviceDetailResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def get_device(
    place_id: UUID,
    device_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.GetDevice(
        GrpcGetDeviceRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    d = response.device
    return DeviceDetailResponse(
        device_id=d.device_id,
        place_id=d.place_id,
        name=d.name,
        status=STATUS_FROM_PROTO.get(d.status, "offline"),
        last_seen_at=d.last_seen_at or None,
        created_at=d.created_at,
        updated_at=d.updated_at,
        sensors=[
            SensorResponse(
                sensor_id=s.sensor_id,
                device_id=s.device_id,
                key=s.key,
                name=s.name,
                value_type=VALUE_TYPE_FROM_PROTO.get(s.value_type, "number"),
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
                value_type=VALUE_TYPE_FROM_PROTO.get(a.value_type, "number"),
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


@router.put(
    "/{device_id}",
    response_model=UpdateDeviceResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def update_device(
    place_id: UUID,
    device_id: UUID,
    body: UpdateDeviceRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateDevice(
        GrpcUpdateDeviceRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            name=body.name,
        )
    )
    return UpdateDeviceResponse(device_id=response.device_id)


@router.delete(
    "/{device_id}",
    response_model=DeleteResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def delete_device(
    place_id: UUID,
    device_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteDevice(
        GrpcDeleteDeviceRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    warnings: list[str] = []
    try:
        await collector_stub.DeleteReadings(DeleteReadingsRequest(device_ids=[str(device_id)]))
    except grpc.aio.AioRpcError:
        logger.warning("Failed to cleanup readings for device %s", device_id)
        warnings.append("Failed to cleanup telemetry readings")
    return DeleteResponse(success=response.success, warnings=warnings)


@router.post(
    "/{device_id}/regenerate-token",
    response_model=RegenerateTokenResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def regenerate_token(
    place_id: UUID,
    device_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.RegenerateDeviceToken(
        GrpcRegenerateDeviceTokenRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    return RegenerateTokenResponse(token=response.token)


# --- Sensors ---


@router.post(
    "/{device_id}/sensors",
    status_code=201,
    response_model=CreateSensorResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **CONFLICT_ERRORS},
)
async def create_sensor(
    place_id: UUID,
    device_id: UUID,
    body: CreateSensorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreateSensor(
        GrpcCreateSensorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            key=body.key,
            name=body.name,
            value_type=VALUE_TYPE_TO_PROTO[body.value_type],
            unit_label=body.unit_label,
            precision=body.precision,
        )
    )
    return CreateSensorResponse(sensor_id=response.sensor_id)


@router.get(
    "/{device_id}/sensors",
    response_model=SensorListResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS},
)
async def list_sensors(
    place_id: UUID,
    device_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListSensors(
        GrpcListSensorsRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    return SensorListResponse(
        sensors=[
            SensorResponse(
                sensor_id=s.sensor_id,
                device_id=s.device_id,
                key=s.key,
                name=s.name,
                value_type=VALUE_TYPE_FROM_PROTO.get(s.value_type, "number"),
                unit_label=s.unit_label,
                precision=s.precision,
            )
            for s in response.sensors
        ]
    )


@router.put(
    "/{device_id}/sensors/{sensor_id}",
    response_model=UpdateSensorResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def update_sensor(
    place_id: UUID,
    device_id: UUID,
    sensor_id: UUID,
    body: UpdateSensorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateSensor(
        GrpcUpdateSensorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
            name=body.name,
            unit_label=body.unit_label,
            precision=body.precision,
        )
    )
    return UpdateSensorResponse(sensor_id=response.sensor_id)


@router.delete(
    "/{device_id}/sensors/{sensor_id}",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def delete_sensor(
    place_id: UUID,
    device_id: UUID,
    sensor_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteSensor(
        GrpcDeleteSensorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
        )
    )
    return SuccessResponse(success=response.success)


# --- Thresholds ---


@router.post(
    "/{device_id}/sensors/{sensor_id}/thresholds",
    status_code=201,
    response_model=SetThresholdResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **CONFLICT_ERRORS},
)
async def set_threshold(
    place_id: UUID,
    device_id: UUID,
    sensor_id: UUID,
    body: SetThresholdRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.SetThreshold(
        GrpcSetThresholdRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
            type=THRESHOLD_TYPE_TO_PROTO[body.type],
            value=body.value,
            severity=SEVERITY_TO_PROTO[body.severity],
        )
    )
    return SetThresholdResponse(threshold_id=response.threshold_id)


@router.get(
    "/{device_id}/sensors/{sensor_id}/thresholds",
    response_model=ThresholdListResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS},
)
async def list_thresholds(
    place_id: UUID,
    device_id: UUID,
    sensor_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListThresholds(
        GrpcListThresholdsRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
        )
    )
    return ThresholdListResponse(
        thresholds=[
            ThresholdResponse(
                threshold_id=t.threshold_id,
                sensor_id=t.sensor_id,
                type=THRESHOLD_TYPE_FROM_PROTO.get(t.type, "min"),
                value=t.value,
                severity=SEVERITY_FROM_PROTO.get(t.severity, "warning"),
            )
            for t in response.thresholds
        ]
    )


@router.delete(
    "/{device_id}/sensors/{sensor_id}/thresholds/{threshold_id}",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def delete_threshold(
    place_id: UUID,
    device_id: UUID,
    sensor_id: UUID,
    threshold_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteThreshold(
        GrpcDeleteThresholdRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
            threshold_id=str(threshold_id),
        )
    )
    return SuccessResponse(success=response.success)


# --- Actuators ---


@router.post(
    "/{device_id}/actuators",
    status_code=201,
    response_model=CreateActuatorResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **CONFLICT_ERRORS},
)
async def create_actuator(
    place_id: UUID,
    device_id: UUID,
    body: CreateActuatorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreateActuator(
        GrpcCreateActuatorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            key=body.key,
            name=body.name,
            value_type=VALUE_TYPE_TO_PROTO[body.value_type],
            unit_label=body.unit_label,
            precision=body.precision,
            min_value=body.min_value if body.min_value is not None else 0,
            max_value=body.max_value if body.max_value is not None else 0,
            step=body.step if body.step is not None else 0,
            enum_options=body.enum_options or [],
        )
    )
    return CreateActuatorResponse(actuator_id=response.actuator_id)


@router.get(
    "/{device_id}/actuators",
    response_model=ActuatorListResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS},
)
async def list_actuators(
    place_id: UUID,
    device_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListActuators(
        GrpcListActuatorsRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    return ActuatorListResponse(
        actuators=[
            ActuatorResponse(
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
            for a in response.actuators
        ]
    )


@router.put(
    "/{device_id}/actuators/{actuator_id}",
    response_model=UpdateActuatorResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def update_actuator(
    place_id: UUID,
    device_id: UUID,
    actuator_id: UUID,
    body: UpdateActuatorRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateActuator(
        GrpcUpdateActuatorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            actuator_id=str(actuator_id),
            name=body.name,
            unit_label=body.unit_label,
            precision=body.precision,
            min_value=body.min_value if body.min_value is not None else 0,
            max_value=body.max_value if body.max_value is not None else 0,
            step=body.step if body.step is not None else 0,
            enum_options=body.enum_options or [],
        )
    )
    return UpdateActuatorResponse(actuator_id=response.actuator_id)


@router.delete(
    "/{device_id}/actuators/{actuator_id}",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def delete_actuator(
    place_id: UUID,
    device_id: UUID,
    actuator_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.DeleteActuator(
        GrpcDeleteActuatorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            actuator_id=str(actuator_id),
        )
    )
    return SuccessResponse(success=response.success)


# --- Commands ---


@router.post(
    "/{device_id}/command",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def send_command(
    place_id: UUID,
    device_id: UUID,
    body: SendCommandBody,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.SendCommand(
        GrpcSendCommandRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            actuator_key=body.actuator_key,
            value=body.value,
        )
    )
    return SuccessResponse(success=response.success)


# --- MQTT credentials ---


@mqtt_router.post(
    "/credentials",
    response_model=MqttCredentialsResponse,
    responses={**AUTH_ERRORS},
)
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
