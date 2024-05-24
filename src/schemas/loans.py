from copy import deepcopy
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class LoanBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    description: str | None = None
    start_date: date | None = None
    interest_rate_percent: Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=4)]
    loan_amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    loan_term: Annotated[int, Field(gt=1)]


class LoanCreate(LoanBase):
    start_date: date

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Unique loan name among user loans",
                "description": "Description of the loan",
                "start_date": "2024-01-01",
                "interest_rate_percent": 10.75,
                "loan_amount": 1_000_000,
                "loan_term": 12,
            }
        }
    )


class LoanUpdate(LoanCreate):
    pass


class LoanRead(LoanBase):
    model_config = deepcopy(LoanCreate.model_config)
    model_config["json_schema_extra"]["example"].update(
        {
            "id": "aa765c23-f699-442b-8910-88ae0eb5cea3",
            "user_id": "00db6ae8-64b4-4d4c-8ee7-84958fc95778",
        }
    )

    id: UUID
    user_id: UUID
