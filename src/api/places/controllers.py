import asyncio
import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts import auth_pb2 as auth_pb
from placebrain_contracts import places_pb2 as places_pb
from placebrain_contracts.auth_pb2_grpc import AuthServiceStub
from placebrain_contracts.places_pb2_grpc import PlacesServiceStub

from src.core.enums import ROLE_FROM_PROTO, ROLE_TO_PROTO, PlaceRole
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
    current_user: AuthenticatedUser,
) -> CreatePlaceResponse:
    response = await stub.CreatePlace(
        places_pb.CreatePlaceRequest(
            user_id=current_user.user_id,
            name=body.name,
            description=body.description,
        )
    )
    return CreatePlaceResponse(place_id=response.place_id)


@router.get(
    "",
    response_model=PlaceListResponse,
    responses={**AUTH_ERRORS},
)
async def list_places(
    stub: FromDishka[PlacesServiceStub],
    current_user: AuthenticatedUser,
) -> PlaceListResponse:
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
) -> PlaceResponse:
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
) -> UpdatePlaceResponse:
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
    current_user: AuthenticatedUser,
) -> DeleteResponse:
    response = await stub.DeletePlace(
        places_pb.DeletePlaceRequest(user_id=current_user.user_id, place_id=str(place_id))
    )
    return DeleteResponse(success=response.success)


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
    current_user: AuthenticatedUser,
) -> SuccessResponse:
    user_response = await auth_stub.GetUserByEmail(auth_pb.GetUserByEmailRequest(email=body.email))
    response = await stub.AddMember(
        places_pb.AddMemberRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            target_user_id=user_response.user_id,
            role=ROLE_TO_PROTO[body.role],  # type: ignore[arg-type]
        )
    )
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
    current_user: AuthenticatedUser,
) -> SuccessResponse:
    response = await stub.RemoveMember(
        places_pb.RemoveMemberRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            target_user_id=str(user_id),
        )
    )
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
) -> SuccessResponse:
    response = await stub.UpdateMemberRole(
        places_pb.UpdateMemberRoleRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            target_user_id=str(user_id),
            role=ROLE_TO_PROTO[body.role],  # type: ignore[arg-type]
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
) -> MemberListResponse:
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
                role=ROLE_FROM_PROTO.get(m.role, PlaceRole.OWNER),
            )
            for m in response.members
        ]
    )
