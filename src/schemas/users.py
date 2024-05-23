from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: Annotated[str, EmailStr]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=6, max_length=64)]


class UserRead(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
