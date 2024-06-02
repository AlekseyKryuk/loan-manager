import logging
from datetime import date
from typing import Sequence
from uuid import UUID

import redis
from fastapi import HTTPException, status
from orjson import orjson
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.config import settings
from src.cache.connection import cache
from src.database.models import User, LoanPayment
from src.database.models.loans import Loan
from src.repositories.loans import LoanRepository
from src.repositories.loan_payments import LoanPaymentRepository
from src.repositories.users import UserRepository
from src.schemas.loans import LoanCreate, LoanRead, LoanUpdate
from src.utils.serialization import orjson_default


logger = logging.getLogger(__name__)


class LoanService:
    @staticmethod
    async def create_loan(session: AsyncSession, email: str, loan_data: LoanCreate) -> LoanRead:
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
            loan_db: Loan = await loan_repo.create(**loan_dict)
        except IntegrityError as e:
            logger.exception(e.args)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'The loan with name "{loan_data.name}" already exists'
            )
        await session.commit()

        loan: LoanRead = LoanRead(**loan_db.__dict__)
        json_loan = orjson.dumps(loan.model_dump(), default=orjson_default)
        try:
            await cache.set(f'user:{email}.loan:{loan.id}', json_loan, ex=settings.cache.ttl)
        except redis.exceptions.ConnectionError:
            pass
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

    @staticmethod
    async def update_loan(
            session: AsyncSession,
            loan_id: UUID,
            email: str,
            data: LoanUpdate,
    ) -> Loan:
        loan_data_dict: dict[str, ...] = data.model_dump(exclude_unset=True)
        loan_repo: LoanRepository = LoanRepository(session=session)
        loan_payment_repo: LoanPaymentRepository = LoanPaymentRepository(session=session)
        payments: Sequence[LoanPayment] = await loan_payment_repo.get_many(loan_id=loan_id, email=email)
        if payments:
            match (data.start_date, data.loan_amount, data.interest_rate_percent, data.loan_term):
                case (None, None, None, None):
                    pass
                case _:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Parameters: start_date, loan_amount, interest_rate_percent, loan_term cannot be "
                               "updated for the loan that already has a schedule, because the schedule "
                               "depends on these parameters."
                    )
        try:
            loan: Loan | None = await loan_repo.update(data=loan_data_dict, id=loan_id, email=email)
        except IntegrityError as e:
            logger.exception(e.args)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'The loan with name "{data.name}" already exists',
            )
        await session.commit()
        return loan
