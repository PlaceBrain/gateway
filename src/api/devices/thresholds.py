from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts import devices_pb2 as devices_pb
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.core.enums import SEVERITY_TO_PROTO, THRESHOLD_TYPE_TO_PROTO
from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import (
    AUTH_ERRORS,
    CONFLICT_ERRORS,
    FORBIDDEN_ERRORS,
    NOT_FOUND_ERRORS,
    SuccessResponse,
)

from .schemas import (
    SetThresholdRequest,
    SetThresholdResponse,
    ThresholdListResponse,
    ThresholdResponse,
)

router = APIRouter(
    prefix="/places/{place_id}/devices/{device_id}/sensors/{sensor_id}/thresholds",
    tags=["thresholds"],
    route_class=DishkaRoute,
)


@router.post(
    "",
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
) -> SetThresholdResponse:
    response = await stub.SetThreshold(
        devices_pb.SetThresholdRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
            type=THRESHOLD_TYPE_TO_PROTO[body.type],  # type: ignore[arg-type]
            value=body.value,
            severity=SEVERITY_TO_PROTO[body.severity],  # type: ignore[arg-type]
        )
    )
    return SetThresholdResponse(threshold_id=response.threshold_id)


@router.get(
    "",
    response_model=ThresholdListResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS},
)
async def list_thresholds(
    place_id: UUID,
    device_id: UUID,
    sensor_id: UUID,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
) -> ThresholdListResponse:
    response = await stub.ListThresholds(
        devices_pb.ListThresholdsRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
        )
    )
    return ThresholdListResponse(
        thresholds=[ThresholdResponse.from_proto(t) for t in response.thresholds]
    )


@router.delete(
    "/{threshold_id}",
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
) -> SuccessResponse:
    response = await stub.DeleteThreshold(
        devices_pb.DeleteThresholdRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            sensor_id=str(sensor_id),
            threshold_id=str(threshold_id),
        )
    )
    return SuccessResponse(success=response.success)
