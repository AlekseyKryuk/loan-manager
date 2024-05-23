from typing import Annotated

from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt_handler import create_access_token
from src.database.models.users import User
from src.schemas.token import Token
from src.schemas.users import UserRead, UserCreate
from src.services.users import UserService
from ..dependencies import get_session


router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
)
async def create_user(
        user_data: UserCreate,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    user_service: UserService = UserService()
    user: User = await user_service.create_user(session=session, user_data=user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
        user_form: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[AsyncSession, Depends(get_session)],
):
    user_service: UserService = UserService()
    user: User = await user_service.login(session=session, user_form=user_form)
    access_token: str = create_access_token(user.email)
    return Token(access_token=access_token)
