from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


type BillionDecimal = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class LoanPaymentBase(BaseModel):
    payment_date: date | None = None
    payment_amount: BillionDecimal | None = None


class LoanPaymentCreate(LoanPaymentBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "payment_date": "2023-12-31", "payment_amount": 100000.00
            }
        }
    )


class LoanPaymentRead(LoanPaymentBase):
    id: UUID
    loan_id: UUID
    payment_number: int
    payment_date: date
    payment_amount: BillionDecimal
    interest_amount: BillionDecimal
    principal_amount: BillionDecimal
    incoming_balance: BillionDecimal
    remaining_balance: Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
