import asyncio
import logging

import grpc
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts.auth_pb2 import GetMeRequest, GetUserByEmailRequest
from placebrain_contracts.auth_pb2_grpc import AuthServiceStub
from placebrain_contracts.collector_pb2 import DeleteReadingsRequest
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.devices_pb2 import (
    DeleteDevicesByPlaceRequest as GrpcDeleteDevicesByPlaceRequest,
)
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub
from placebrain_contracts.places_pb2 import (
    AddMemberRequest as GrpcAddMemberRequest,
)
from placebrain_contracts.places_pb2 import (
    CreatePlaceRequest as GrpcCreatePlaceRequest,
)
from placebrain_contracts.places_pb2 import (
    DeletePlaceRequest as GrpcDeletePlaceRequest,
)
from placebrain_contracts.places_pb2 import (
    GetPlaceRequest as GrpcGetPlaceRequest,
)
from placebrain_contracts.places_pb2 import (
    ListMembersRequest as GrpcListMembersRequest,
)
from placebrain_contracts.places_pb2 import (
    ListPlacesRequest as GrpcListPlacesRequest,
)
from placebrain_contracts.places_pb2 import (
    RemoveMemberRequest as GrpcRemoveMemberRequest,
)
from placebrain_contracts.places_pb2 import (
    UpdateMemberRoleRequest as GrpcUpdateMemberRoleRequest,
)
from placebrain_contracts.places_pb2 import (
    UpdatePlaceRequest as GrpcUpdatePlaceRequest,
)
from placebrain_contracts.places_pb2_grpc import PlacesServiceStub

from src.api.enums import ROLE_MAP, ROLE_REVERSE, resolve_enum
from src.dependencies.auth import AuthenticatedUser

from .schemas import (
    AddMemberRequest,
    CreatePlaceRequest,
    CreatePlaceResponse,
    DeletePlaceResponse,
    MemberListResponse,
    MemberResponse,
    PlaceListResponse,
    PlaceResponse,
    SuccessResponse,
    UpdateMemberRoleRequest,
    UpdatePlaceRequest,
    UpdatePlaceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places", tags=["places"], route_class=DishkaRoute)


@router.post("", response_model=CreatePlaceResponse)
async def create_place(
    body: CreatePlaceRequest,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.CreatePlace(
        GrpcCreatePlaceRequest(
            user_id=current_user.user_id,
            name=body.name,
            description=body.description,
        )
    )
    return CreatePlaceResponse(place_id=response.place_id)


@router.get("", response_model=PlaceListResponse)
async def list_places(
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListPlaces(GrpcListPlacesRequest(user_id=current_user.user_id))
    return PlaceListResponse(
        places=[
            PlaceResponse(
                place_id=p.place_id,
                name=p.name,
                description=p.description,
                user_role=ROLE_MAP.get(p.user_role, "unspecified"),
            )
            for p in response.places
        ]
    )


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: str,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.GetPlace(
        GrpcGetPlaceRequest(user_id=current_user.user_id, place_id=place_id)
    )
    return PlaceResponse(
        place_id=response.place_id,
        name=response.name,
        description=response.description,
        user_role=ROLE_MAP.get(response.user_role, "unspecified"),
    )


@router.put("/{place_id}", response_model=UpdatePlaceResponse)
async def update_place(
    place_id: str,
    body: UpdatePlaceRequest,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdatePlace(
        GrpcUpdatePlaceRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            name=body.name,
            description=body.description,
        )
    )
    return UpdatePlaceResponse(place_id=response.place_id)


@router.delete("/{place_id}", response_model=DeletePlaceResponse)
async def delete_place(
    place_id: str,
    stub: FromDishka[PlacesServiceStub],
    devices_stub: FromDishka[DevicesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
):
    await stub.DeletePlace(GrpcDeletePlaceRequest(user_id=current_user.user_id, place_id=place_id))
    warnings: list[str] = []
    try:
        response = await devices_stub.DeleteDevicesByPlace(
            GrpcDeleteDevicesByPlaceRequest(place_id=place_id)
        )
        if response.device_ids:
            try:
                await collector_stub.DeleteReadings(
                    DeleteReadingsRequest(device_ids=response.device_ids)
                )
            except grpc.aio.AioRpcError:
                logger.warning("Failed to cleanup readings for place %s", place_id)
                warnings.append("Failed to cleanup telemetry readings")
    except grpc.aio.AioRpcError:
        logger.warning("Failed to cleanup devices for place %s", place_id)
        warnings.append("Failed to cleanup devices and their readings")
    return DeletePlaceResponse(success=True, warnings=warnings)


@router.post("/{place_id}/members", response_model=SuccessResponse)
async def add_member(
    place_id: str,
    body: AddMemberRequest,
    stub: FromDishka[PlacesServiceStub],
    auth_stub: FromDishka[AuthServiceStub],
    current_user: AuthenticatedUser,
):
    user_response = await auth_stub.GetUserByEmail(GetUserByEmailRequest(email=body.email))
    response = await stub.AddMember(
        GrpcAddMemberRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            target_user_id=user_response.user_id,
            role=resolve_enum(ROLE_REVERSE, body.role, "role"),
        )
    )
    return SuccessResponse(success=response.success)


@router.delete("/{place_id}/members/{user_id}", response_model=SuccessResponse)
async def remove_member(
    place_id: str,
    user_id: str,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.RemoveMember(
        GrpcRemoveMemberRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            target_user_id=user_id,
        )
    )
    return SuccessResponse(success=response.success)


@router.put("/{place_id}/members/{user_id}", response_model=SuccessResponse)
async def update_member_role(
    place_id: str,
    user_id: str,
    body: UpdateMemberRoleRequest,
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.UpdateMemberRole(
        GrpcUpdateMemberRoleRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            target_user_id=user_id,
            role=resolve_enum(ROLE_REVERSE, body.role, "role"),
        )
    )
    return SuccessResponse(success=response.success)


@router.get("/{place_id}/members", response_model=MemberListResponse)
async def list_members(
    place_id: str,
    stub: FromDishka[PlacesServiceStub],
    auth_stub: FromDishka[AuthServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.ListMembers(
        GrpcListMembersRequest(user_id=current_user.user_id, place_id=place_id)
    )

    user_infos = await asyncio.gather(
        *(auth_stub.GetMe(GetMeRequest(user_id=m.user_id)) for m in response.members)
    )
    username_map = {info.user_id: info.username for info in user_infos}

    return MemberListResponse(
        members=[
            MemberResponse(
                user_id=m.user_id,
                username=username_map.get(m.user_id, m.user_id),
                role=ROLE_MAP.get(m.role, "unspecified"),
            )
            for m in response.members
        ]
    )
