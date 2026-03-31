import logging
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from placebrain_contracts.auth_pb2 import (
    GetMeRequest,
    RefreshTokensRequest,
)
from placebrain_contracts.auth_pb2 import (
    LoginRequest as GrpcLoginRequest,
)
from placebrain_contracts.auth_pb2 import (
    LogoutRequest as GrpcLogoutRequest,
)
from placebrain_contracts.auth_pb2 import (
    RegisterRequest as GrpcRegisterRequest,
)
from placebrain_contracts.auth_pb2 import (
    SendOtpRequest as GrpcSendOtpRequest,
)
from placebrain_contracts.auth_pb2 import (
    VerifyOtpRequest as GrpcVerifyOtpRequest,
)
from placebrain_contracts.auth_pb2_grpc import AuthServiceStub

from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import AUTH_ERRORS, CONFLICT_ERRORS, SuccessResponse

from .schemas import (
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    SendOtpRequest,
    TokenResponse,
    UserResponse,
    VerifyOtpRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)


@router.post(
    "/register", status_code=201, response_model=RegisterResponse, responses={**CONFLICT_ERRORS}
)
async def register(body: RegisterRequest, stub: FromDishka[AuthServiceStub]):
    response = await stub.Register(
        GrpcRegisterRequest(username=body.username, email=body.email, password=body.password)
    )
    try:
        await stub.SendOtp(GrpcSendOtpRequest(email=body.email))
    except Exception:
        logger.warning("Failed to send OTP after registration for %s", body.email)
    return RegisterResponse(user_id=response.user_id)


@router.post("/login", response_model=TokenResponse, responses={**AUTH_ERRORS})
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)],
    stub: FromDishka[AuthServiceStub],
):
    response = await stub.Login(
        GrpcLoginRequest(email=form_data.username, password=form_data.password)
    )
    return TokenResponse(access_token=response.access_token, refresh_token=response.refresh_token)


@router.post("/refresh", response_model=TokenResponse, responses={**AUTH_ERRORS})
async def refresh(body: RefreshRequest, stub: FromDishka[AuthServiceStub]):
    response = await stub.RefreshTokens(RefreshTokensRequest(refresh_token=body.refresh_token))
    return TokenResponse(access_token=response.access_token, refresh_token=response.refresh_token)


@router.post("/logout", response_model=SuccessResponse)
async def logout(body: LogoutRequest, stub: FromDishka[AuthServiceStub]):
    response = await stub.Logout(GrpcLogoutRequest(refresh_token=body.refresh_token))
    return SuccessResponse(success=response.success)


@router.get("/me", response_model=UserResponse, responses={**AUTH_ERRORS})
async def get_me(
    stub: FromDishka[AuthServiceStub],
    current_user: AuthenticatedUser,
):
    response = await stub.GetMe(GetMeRequest(user_id=current_user.user_id))
    return UserResponse(
        user_id=response.user_id,
        username=response.username,
        email=response.email,
        is_verified=response.is_verified,
    )


@router.post("/send-otp", response_model=SuccessResponse)
async def send_otp(body: SendOtpRequest, stub: FromDishka[AuthServiceStub]):
    response = await stub.SendOtp(GrpcSendOtpRequest(email=body.email))
    return SuccessResponse(success=response.success)


@router.post("/verify-otp", response_model=SuccessResponse)
async def verify_otp(body: VerifyOtpRequest, stub: FromDishka[AuthServiceStub]):
    response = await stub.VerifyOtp(GrpcVerifyOtpRequest(email=body.email, code=body.code))
    return SuccessResponse(success=response.success)
