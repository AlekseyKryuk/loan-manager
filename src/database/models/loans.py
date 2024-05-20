from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import Base, uuid_pk


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid_pk]
    name: Mapped[str]
    description: Mapped[str | None]
    start_date: Mapped[date]
    interest_rate_percent: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    loan_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    loan_term: Mapped[int]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("user_id", "name"),
    )
