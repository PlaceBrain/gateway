import asyncio
import logging
from uuid import UUID

import grpc
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts import auth_pb2 as auth_pb
from placebrain_contracts import collector_pb2 as collector_pb
from placebrain_contracts import devices_pb2 as devices_pb
from placebrain_contracts import places_pb2 as places_pb
from placebrain_contracts.auth_pb2_grpc import AuthServiceStub
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub
from placebrain_contracts.places_pb2_grpc import PlacesServiceStub

from src.core.enums import ROLE_FROM_PROTO, ROLE_TO_PROTO
from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import (
    AUTH_ERRORS,
    CONFLICT_ERRORS,
    FORBIDDEN_ERRORS,
    NOT_FOUND_ERRORS,
    DeleteResponse,
    SuccessResponse,
)

from .schemas import (
    AddMemberRequest,
    CreatePlaceRequest,
    CreatePlaceResponse,
    MemberListResponse,
    MemberResponse,
    PlaceListResponse,
    PlaceResponse,
    UpdateMemberRoleRequest,
    UpdatePlaceRequest,
    UpdatePlaceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places", tags=["places"], route_class=DishkaRoute)


@router.post(
    "",
    status_code=201,
    response_model=CreatePlaceResponse,
    responses={**AUTH_ERRORS, **CONFLICT_ERRORS},
)
async def create_place(
    body: CreatePlaceRequest,
    stub: FromDishka[PlacesServiceStub],
    devices_stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreatePlace(
        places_pb.CreatePlaceRequest(
            user_id=current_user.user_id,
            name=body.name,
            description=body.description,
        )
    )
    try:
        await devices_stub.InvalidateMqttCredentials(
            devices_pb.InvalidateMqttCredentialsRequest(user_ids=[current_user.user_id])
        )
    except grpc.aio.AioRpcError:
        logger.warning("Failed to invalidate MQTT credentials for user %s", current_user.user_id)
    return CreatePlaceResponse(place_id=response.place_id)


@router.get(
    "",
    response_model=PlaceListResponse,
    responses={**AUTH_ERRORS},
)
async def list_places(
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListPlaces(places_pb.ListPlacesRequest(user_id=current_user.user_id))
    return PlaceListResponse(places=[PlaceResponse.from_proto(p) for p in response.places])


@router.get(
    "/{place_id}",
    response_model=PlaceResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def get_place(
    place_id: UUID,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.GetPlace(
        places_pb.GetPlaceRequest(user_id=current_user.user_id, place_id=str(place_id))
    )
    return PlaceResponse.from_proto(response)


@router.put(
    "/{place_id}",
    response_model=UpdatePlaceResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def update_place(
    place_id: UUID,
    body: UpdatePlaceRequest,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdatePlace(
        places_pb.UpdatePlaceRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            name=body.name,
            description=body.description,
        )
    )
    return UpdatePlaceResponse(place_id=response.place_id)


@router.delete(
    "/{place_id}",
    response_model=DeleteResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def delete_place(
    place_id: UUID,
    stub: FromDishka[PlacesServiceStub],
    devices_stub: FromDishka[DevicesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
):
    members_response = await stub.ListMembers(
        places_pb.ListMembersRequest(user_id=current_user.user_id, place_id=str(place_id))
    )
    member_user_ids = [m.user_id for m in members_response.members]

    await stub.DeletePlace(
        places_pb.DeletePlaceRequest(user_id=current_user.user_id, place_id=str(place_id))
    )
    warnings: list[str] = []
    try:
        response = await devices_stub.DeleteDevicesByPlace(
            devices_pb.DeleteDevicesByPlaceRequest(place_id=str(place_id))
        )
        if response.device_ids:
            try:
                await collector_stub.DeleteReadings(
                    collector_pb.DeleteReadingsRequest(device_ids=response.device_ids)
                )
            except grpc.aio.AioRpcError:
                logger.warning("Failed to cleanup readings for place %s", place_id)
                warnings.append("Failed to cleanup telemetry readings")
    except grpc.aio.AioRpcError:
        logger.warning("Failed to cleanup devices for place %s", place_id)
        warnings.append("Failed to cleanup devices and their readings")
    if member_user_ids:
        try:
            await devices_stub.InvalidateMqttCredentials(
                devices_pb.InvalidateMqttCredentialsRequest(user_ids=member_user_ids)
            )
        except grpc.aio.AioRpcError:
            logger.warning("Failed to invalidate MQTT credentials for place %s members", place_id)
            warnings.append("Failed to invalidate MQTT credentials")
    return DeleteResponse(success=True, warnings=warnings)


@router.post(
    "/{place_id}/members",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS, **CONFLICT_ERRORS},
)
async def add_member(
    place_id: UUID,
    body: AddMemberRequest,
    stub: FromDishka[PlacesServiceStub],
    auth_stub: FromDishka[AuthServiceStub],
    devices_stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    user_response = await auth_stub.GetUserByEmail(auth_pb.GetUserByEmailRequest(email=body.email))
    response = await stub.AddMember(
        places_pb.AddMemberRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            target_user_id=user_response.user_id,
            role=ROLE_TO_PROTO[body.role],
        )
    )
    try:
        await devices_stub.InvalidateMqttCredentials(
            devices_pb.InvalidateMqttCredentialsRequest(user_ids=[user_response.user_id])
        )
    except grpc.aio.AioRpcError:
        logger.warning("Failed to invalidate MQTT credentials for user %s", user_response.user_id)
    return SuccessResponse(success=response.success)


@router.delete(
    "/{place_id}/members/{user_id}",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def remove_member(
    place_id: UUID,
    user_id: UUID,
    stub: FromDishka[PlacesServiceStub],
    devices_stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.RemoveMember(
        places_pb.RemoveMemberRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            target_user_id=str(user_id),
        )
    )
    try:
        await devices_stub.InvalidateMqttCredentials(
            devices_pb.InvalidateMqttCredentialsRequest(user_ids=[str(user_id)])
        )
    except grpc.aio.AioRpcError:
        logger.warning("Failed to invalidate MQTT credentials for user %s", user_id)
    return SuccessResponse(success=response.success)


@router.put(
    "/{place_id}/members/{user_id}",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def update_member_role(
    place_id: UUID,
    user_id: UUID,
    body: UpdateMemberRoleRequest,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateMemberRole(
        places_pb.UpdateMemberRoleRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            target_user_id=str(user_id),
            role=ROLE_TO_PROTO[body.role],
        )
    )
    return SuccessResponse(success=response.success)


@router.get(
    "/{place_id}/members",
    response_model=MemberListResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def list_members(
    place_id: UUID,
    stub: FromDishka[PlacesServiceStub],
    auth_stub: FromDishka[AuthServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListMembers(
        places_pb.ListMembersRequest(user_id=current_user.user_id, place_id=str(place_id))
    )

    user_infos = await asyncio.gather(
        *(auth_stub.GetMe(auth_pb.GetMeRequest(user_id=m.user_id)) for m in response.members)
    )
    username_map = {info.user_id: info.username for info in user_infos}

    return MemberListResponse(
        members=[
            MemberResponse(
                user_id=m.user_id,
                username=username_map.get(m.user_id, m.user_id),
                role=ROLE_FROM_PROTO.get(m.role, "owner"),
            )
            for m in response.members
        ]
    )
