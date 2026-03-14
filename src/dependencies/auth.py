from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.core.config import settings
from src.schemas.auth import CurrentUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return CurrentUser(
            user_id=payload["sub"],
            email=payload["email"],
            username=payload["username"],
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
