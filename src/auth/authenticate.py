from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .jwt_handler import verify_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


async def authenticate(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='It is necessary to sign in to get access.'
        )
    username: str = await verify_access_token(token)
    return username
