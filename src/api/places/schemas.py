from pydantic import BaseModel


class CreatePlaceRequest(BaseModel):
    name: str
    description: str = ""


class CreatePlaceResponse(BaseModel):
    place_id: str


class PlaceResponse(BaseModel):
    place_id: str
    name: str
    description: str
    user_role: str


class PlaceListResponse(BaseModel):
    places: list[PlaceResponse]


class UpdatePlaceRequest(BaseModel):
    name: str
    description: str


class UpdatePlaceResponse(BaseModel):
    place_id: str


class DeletePlaceResponse(BaseModel):
    success: bool


class AddMemberRequest(BaseModel):
    email: str
    role: str


class MemberResponse(BaseModel):
    user_id: str
    username: str
    role: str


class MemberListResponse(BaseModel):
    members: list[MemberResponse]


class SuccessResponse(BaseModel):
    success: bool


class UpdateMemberRoleRequest(BaseModel):
    role: str
