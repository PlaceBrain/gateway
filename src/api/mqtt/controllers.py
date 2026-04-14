import logging

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
from placebrain_contracts import devices_pb2 as devices_pb
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import AUTH_ERRORS

from .schemas import MqttAclRequest, MqttAuthRequest, MqttCredentialsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mqtt", tags=["mqtt"], route_class=DishkaRoute)

internal_router = APIRouter(
    prefix="/internal/mqtt",
    tags=["mqtt-internal"],
    route_class=DishkaRoute,
    include_in_schema=False,
)


@router.post(
    "/credentials",
    response_model=MqttCredentialsResponse,
    responses={**AUTH_ERRORS},
)
async def generate_mqtt_credentials(
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.GenerateMqttCredentials(
        devices_pb.GenerateMqttCredentialsRequest(user_id=current_user.user_id)
    )
    return MqttCredentialsResponse(
        username=response.username,
        password=response.password,
        expires_at=response.expires_at,
    )


@internal_router.post("/auth")
async def mqtt_auth(
    body: MqttAuthRequest,
    stub: FromDishka[DevicesServiceStub],
):
    response = await stub.AuthenticateDevice(
        devices_pb.AuthenticateDeviceRequest(username=body.username, password=body.password)
    )
    if response.allow:
        return ORJSONResponse(content={"result": "allow"})
    return ORJSONResponse(content={"result": "deny"}, status_code=200)


@internal_router.post("/acl")
async def mqtt_acl(
    body: MqttAclRequest,
    stub: FromDishka[DevicesServiceStub],
):
    response = await stub.CheckDeviceAcl(
        devices_pb.CheckDeviceAclRequest(
            username=body.username, topic=body.topic, action=body.action
        )
    )
    if response.allow:
        return ORJSONResponse(content={"result": "allow"})
    return ORJSONResponse(content={"result": "deny"}, status_code=200)
