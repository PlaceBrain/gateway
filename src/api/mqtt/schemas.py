from pydantic import BaseModel


class MqttAuthRequest(BaseModel):
    username: str
    password: str


class MqttAclRequest(BaseModel):
    username: str
    topic: str
    action: str


class MqttCredentialsResponse(BaseModel):
    username: str
    password: str
    expires_at: int
