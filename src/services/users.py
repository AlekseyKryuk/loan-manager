import logging

from fastapi import status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.hash_password import hash_password
from src.database.models import User
from src.repositories.users import UserRepository
from src.schemas.users import UserCreate


logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    async def create_user(
            session: AsyncSession, user_data: UserCreate
    ) -> User:
        user_repo: UserRepository = UserRepository(session=session)
        db_user: User | None = await user_repo.get(email=user_data.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with supplied email already exists",
            )
        hashed_password: str = hash_password.create_hash(user_data.password)
        created_user: User = await user_repo.create(
            email=user_data.email,
            hashed_password=hashed_password,
        )
        await session.commit()
        return created_user

    @staticmethod
    async def login(
            session: AsyncSession, user_form: OAuth2PasswordRequestForm
    ) -> User:
        incorrect_credentials: HTTPException = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
        )
        user_repo: UserRepository = UserRepository(session=session)
        user: User | None = await user_repo.get(email=user_form.username)
        if not user:
            try:
                raise incorrect_credentials
            except HTTPException as e:
                logger.exception(e.args)
                raise
        if not (
            user.is_active
            and hash_password.verify_hash(user_form.password, user.hashed_password)
        ):
            raise incorrect_credentials
        return user
