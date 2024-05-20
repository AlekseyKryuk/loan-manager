from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))


uuid_pk = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]
