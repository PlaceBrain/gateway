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
    ActuatorListResponse,
    ActuatorResponse,
    CreateActuatorRequest,
    CreateActuatorResponse,
    UpdateActuatorRequest,
    UpdateActuatorResponse,
)

router = APIRouter(
    prefix="/places/{place_id}/devices/{device_id}/actuators",
    tags=["actuators"],
    route_class=DishkaRoute,
)


@router.post(
    "",
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
        devices_pb.CreateActuatorRequest(
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
    "",
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
        devices_pb.ListActuatorsRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    return ActuatorListResponse(
        actuators=[ActuatorResponse.from_proto(a) for a in response.actuators]
    )


@router.put(
    "/{actuator_id}",
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
        devices_pb.UpdateActuatorRequest(
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
    "/{actuator_id}",
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
        devices_pb.DeleteActuatorRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            actuator_id=str(actuator_id),
        )
    )
    return SuccessResponse(success=response.success)
