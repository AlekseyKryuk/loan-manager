from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base_model import Base, uuid_pk


class LoanPayment(Base):
    __tablename__ = "loan_payments"

    id: Mapped[uuid_pk]
    loan_id: Mapped[UUID] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"))
    payment_number: Mapped[int]
    payment_date: Mapped[date]
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    incoming_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    year_part: Mapped[Decimal] = mapped_column(Numeric(33, 32))
    days_in_year: Mapped[int]

    __table_args__ = (
        UniqueConstraint("loan_id", "payment_number"),
        UniqueConstraint("loan_id", "payment_date"),
    )
