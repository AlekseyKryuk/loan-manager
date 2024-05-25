import logging
from datetime import date
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.database.models import User
from src.database.models.loans import Loan
from src.repositories.loans import LoanRepository
from src.repositories.users import UserRepository
from src.schemas.loans import LoanCreate, LoanRead

logger = logging.getLogger(__name__)


class LoanService:
    @staticmethod
    async def create_loan(session: AsyncSession, email: str, loan_data: LoanCreate) -> Loan:
        loan_repo: LoanRepository = LoanRepository(session=session)
        user_repo: UserRepository = UserRepository(session=session)
        user: User | None = await user_repo.get(email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if loan_data.start_date is None:
            loan_data.start_date = date.today()
        loan_dict: dict[str, ...] = loan_data.model_dump()
        loan_dict["user_id"] = user.id
        try:
            loan: Loan = await loan_repo.create(**loan_dict)
        except IntegrityError as e:
            logger.exception(e.args)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'The loan with name "{loan_data.name}" already exists'
            )
        await session.commit()
        return loan

    @staticmethod
    async def get_all_loans(session: AsyncSession, email: str) -> list[LoanRead]:
        loan_repo: LoanRepository = LoanRepository(session=session)
        loans: Sequence[Loan] = await loan_repo.get_all(email=email)
        return [LoanRead(**loan.__dict__) for loan in loans]

    @staticmethod
    async def get_loan(session: AsyncSession, loan_id: UUID, email: str) -> Loan:
        loan_repo: LoanRepository = LoanRepository(session=session)
        loan: Loan | None = await loan_repo.get(id=loan_id, email=email)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The loan with supplied ID doesn't exist"
            )
        return loan

    @staticmethod
    async def delete_loan(session: AsyncSession, loan_id: UUID, email: str) -> Loan:
        loan_repo: LoanRepository = LoanRepository(session=session)
        loan: Loan | None = await loan_repo.delete(id=loan_id, email=email)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The loan with supplied ID doesn't exist"
            )
        await session.commit()
        return loan
