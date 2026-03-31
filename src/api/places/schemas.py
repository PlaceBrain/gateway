from uuid import UUID

from pydantic import BaseModel

from src.api.enums import PlaceRole


class CreatePlaceRequest(BaseModel):
    name: str
    description: str = ""


class CreatePlaceResponse(BaseModel):
    place_id: UUID


class PlaceResponse(BaseModel):
    place_id: UUID
    name: str
    description: str
    user_role: PlaceRole


class PlaceListResponse(BaseModel):
    places: list[PlaceResponse]


class UpdatePlaceRequest(BaseModel):
    name: str
    description: str


class UpdatePlaceResponse(BaseModel):
    place_id: UUID


class AddMemberRequest(BaseModel):
    email: str
    role: PlaceRole


class MemberResponse(BaseModel):
    user_id: UUID
    username: str
    role: PlaceRole


class MemberListResponse(BaseModel):
    members: list[MemberResponse]


class UpdateMemberRoleRequest(BaseModel):
    role: PlaceRole
