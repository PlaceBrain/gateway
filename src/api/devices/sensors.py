from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts import devices_pb2 as devices_pb
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.core.enums import VALUE_TYPE_TO_PROTO
from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import (
    AUTH_ERRORS,
    CONFLICT_ERRORS,
    FORBIDDEN_ERRORS,
    NOT_FOUND_ERRORS,
    SuccessResponse,
)

from .schemas import (
    CreateSensorRequest,
    CreateSensorResponse,
    SensorListResponse,
    SensorResponse,
    UpdateSensorRequest,
    UpdateSensorResponse,
)

router = APIRouter(
    prefix="/places/{place_id}/devices/{device_id}/sensors",
    tags=["sensors"],
    route_class=DishkaRoute,
)


@router.post(
    "",
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
) -> CreateSensorResponse:
    response = await stub.CreateSensor(
        devices_pb.CreateSensorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            key=body.key,
            name=body.name,
            value_type=VALUE_TYPE_TO_PROTO[body.value_type],  # type: ignore[arg-type]
            unit_label=body.unit_label,
            precision=body.precision,
        )
    )
    return CreateSensorResponse(sensor_id=response.sensor_id)


@router.get(
    "",
    response_model=SensorListResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS},
)
async def list_sensors(
    place_id: UUID,
    device_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
) -> SensorListResponse:
    response = await stub.ListSensors(
        devices_pb.ListSensorsRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    return SensorListResponse(sensors=[SensorResponse.from_proto(s) for s in response.sensors])


@router.put(
    "/{sensor_id}",
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
) -> UpdateSensorResponse:
    response = await stub.UpdateSensor(
        devices_pb.UpdateSensorRequest(
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
    "/{sensor_id}",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def delete_sensor(
    place_id: UUID,
    device_id: UUID,
    sensor_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
) -> SuccessResponse:
    response = await stub.DeleteSensor(
        devices_pb.DeleteSensorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
        )
    )
    return SuccessResponse(success=response.success)
