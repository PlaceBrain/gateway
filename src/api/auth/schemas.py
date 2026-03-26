from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class RegisterResponse(BaseModel):
    user_id: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    success: bool


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    is_verified: bool


class SendOtpRequest(BaseModel):
    email: str


class SendOtpResponse(BaseModel):
    success: bool


class VerifyOtpRequest(BaseModel):
    email: str
    code: str


class VerifyOtpResponse(BaseModel):
    success: bool
