import logging
from datetime import timedelta, datetime, UTC

from fastapi import HTTPException, status
from jose import jwt, JWTError

from src.config import settings


logger = logging.getLogger(__name__)


def create_access_token(
        user: str,
        expires_delta: timedelta = timedelta(minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES)
) -> str:
    expire: datetime = datetime.now(UTC) + expires_delta
    payload = {
        'sub': user,
        'exp': expire
    }
    token: str = jwt.encode(
        payload,
        settings.auth.SECRET_KEY,
        algorithm=settings.auth.ALGORITHM
    )
    return token


async def verify_access_token(token: str) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.auth.SECRET_KEY,
            settings.auth.ALGORITHM
        )

        expired_at: int = payload.get("exp")
        username: str = payload.get("sub")

        if expired_at is None or username is None:
            raise credentials_exception

        if datetime.now(UTC) > datetime.fromtimestamp(expired_at, UTC):
            raise credentials_exception

        return username

    except JWTError as e:
        logger.exception(e)
        raise credentials_exception