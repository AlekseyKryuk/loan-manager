from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_session, authenticate
from src.config import settings
from src.database.models.loans import Loan
from src.schemas.loans import LoanCreate, LoanRead, LoanUpdate
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


@router.get("/{loan_id}", response_model=LoanRead)
async def get_loan(
        loan_id: Annotated[UUID, Path()],
        email: Annotated[str, Depends(authenticate)],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> LoanRead:
    loan_service: LoanService = LoanService()
    loan: Loan = await loan_service.get_loan(session=session, loan_id=loan_id, email=email)
    return LoanRead(**loan.__dict__)


@router.delete("/{loan_id}", response_model=dict[str, str])
async def delete_loan(
        loan_id: Annotated[UUID, Path()],
        session: Annotated[AsyncSession, Depends(get_session)],
        email: Annotated[str, Depends(authenticate)],
) -> dict[str, str]:
    loan_service: LoanService = LoanService()
    loan: Loan = await loan_service.delete_loan(session=session, loan_id=loan_id, email=email)
    return {"message": f"The loan with name {loan.name} was deleted successfully"}


@router.put("/{loan_id}", response_model=LoanRead)
async def update_loan(
        loan_id: Annotated[UUID, Path()],
        loan_data: Annotated[LoanUpdate, Body()],
        email: Annotated[str, Depends(authenticate)],
        session: Annotated[AsyncSession, Depends(get_session)],
) -> LoanRead:
    loan_service: LoanService = LoanService()
    loan: Loan = await loan_service.update_loan(
        session=session,
        loan_id=loan_id,
        email=email,
        data=loan_data,
    )
    return LoanRead(**loan.__dict__)
