import logging
from uuid import UUID

import grpc
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts import collector_pb2 as collector_pb
from placebrain_contracts import devices_pb2 as devices_pb
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.core.enums import STATUS_FROM_PROTO, DeviceStatus
from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import (
    AUTH_ERRORS,
    CONFLICT_ERRORS,
    FORBIDDEN_ERRORS,
    NOT_FOUND_ERRORS,
    DeleteResponse,
    PaginatedResponse,
    PaginationParams,
)

from .schemas import (
    ActuatorResponse,
    CreateDeviceRequest,
    CreateDeviceResponse,
    DeviceDetailResponse,
    DeviceSummaryResponse,
    RegenerateTokenResponse,
    SensorResponse,
    UpdateDeviceRequest,
    UpdateDeviceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places/{place_id}/devices", tags=["devices"], route_class=DishkaRoute)


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
) -> CreateDeviceResponse:
    response = await stub.CreateDevice(
        devices_pb.CreateDeviceRequest(
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
) -> PaginatedResponse[DeviceSummaryResponse]:
    response = await stub.ListDevices(
        devices_pb.ListDevicesRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            page=pagination.page,
            per_page=pagination.per_page,
        )
    )
    return PaginatedResponse(
        items=[DeviceSummaryResponse.from_proto(d) for d in response.devices],
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
) -> DeviceDetailResponse:
    response = await stub.GetDevice(
        devices_pb.GetDeviceRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    d = response.device
    return DeviceDetailResponse(
        device_id=d.device_id,
        place_id=d.place_id,
        name=d.name,
        status=STATUS_FROM_PROTO.get(d.status, DeviceStatus.OFFLINE),
        last_seen_at=d.last_seen_at or None,
        created_at=d.created_at,
        updated_at=d.updated_at,
        sensors=[SensorResponse.from_proto(s) for s in d.sensors],
        actuators=[ActuatorResponse.from_proto(a) for a in d.actuators],
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
) -> UpdateDeviceResponse:
    response = await stub.UpdateDevice(
        devices_pb.UpdateDeviceRequest(
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
) -> DeleteResponse:
    response = await stub.DeleteDevice(
        devices_pb.DeleteDeviceRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    warnings: list[str] = []
    try:
        await collector_stub.DeleteReadings(
            collector_pb.DeleteReadingsRequest(device_ids=[str(device_id)])
        )
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
) -> RegenerateTokenResponse:
    response = await stub.RegenerateDeviceToken(
        devices_pb.RegenerateDeviceTokenRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )
    return RegenerateTokenResponse(token=response.token)
