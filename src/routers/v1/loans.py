from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_session, authenticate
from src.config import settings
from src.database.models.loans import Loan
from src.schemas.loans import LoanCreate, LoanRead
from src.services.loans import LoanService


router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=LoanRead)
async def create_loan(
        loan_data: Annotated[LoanCreate, Body()],
        username: Annotated[str, Depends(authenticate)],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> Loan:
    loan_service: LoanService = LoanService()
    new_loan: Loan = await loan_service.create_loan(session=session, username=username, loan_data=loan_data)
    return new_loan
