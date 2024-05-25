from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Body, status
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
        email: Annotated[str, Depends(authenticate)],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> LoanRead:
    loan_service: LoanService = LoanService()
    new_loan: Loan = await loan_service.create_loan(session=session, email=email, loan_data=loan_data)
    return LoanRead(**new_loan.__dict__)


@router.get("/", response_model=list[LoanRead])
async def get_all_loans(
        email: Annotated[str, Depends(authenticate)],
        session: Annotated[AsyncSession, Depends(get_session)],
        limit: Annotated[int, Query] = settings.pagination.limit,
        offset: Annotated[int, Query] = settings.pagination.offset,
) -> list[LoanRead]:
    loan_service: LoanService = LoanService()
    loans: list[LoanRead] = await loan_service.get_all_loans(session=session, email=email)
    return loans[offset:offset+limit]
