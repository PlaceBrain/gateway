import logging

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
from placebrain_contracts.devices_pb2 import (
    AuthenticateDeviceRequest as GrpcAuthenticateDeviceRequest,
)
from placebrain_contracts.devices_pb2 import (
    CheckDeviceAclRequest as GrpcCheckDeviceAclRequest,
)
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from .schemas import MqttAclRequest, MqttAuthRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/internal/mqtt",
    tags=["mqtt-internal"],
    route_class=DishkaRoute,
    include_in_schema=False,
)


@router.post("/auth")
async def mqtt_auth(
    body: MqttAuthRequest,
    stub: FromDishka[DevicesServiceStub],
):
    response = await stub.AuthenticateDevice(
        GrpcAuthenticateDeviceRequest(username=body.username, password=body.password)
    )
    if response.allow:
        return ORJSONResponse(content={"result": "allow"})
    return ORJSONResponse(content={"result": "deny"}, status_code=200)


@router.post("/acl")
async def mqtt_acl(
    body: MqttAclRequest,
    stub: FromDishka[DevicesServiceStub],
):
    response = await stub.CheckDeviceAcl(
        GrpcCheckDeviceAclRequest(username=body.username, topic=body.topic, action=body.action)
    )
    if response.allow:
        return ORJSONResponse(content={"result": "allow"})
    return ORJSONResponse(content={"result": "deny"}, status_code=200)
