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
        json_loan: bytes = orjson.dumps(loan.model_dump(), default=orjson_default)
        try:
            await cache.set(f'user:{email}.loan:{loan.id}', json_loan, ex=settings.cache.ttl)
            await cache.delete(f'user:{email}.loans')
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)
        return loan

    @staticmethod
    async def get_all_loans(session: AsyncSession, email: str) -> list[LoanRead]:
        loan_repo: LoanRepository = LoanRepository(session=session)
        loans: list[LoanRead]

        try:
            loans_cache: bytes = await cache.get(f'user:{email}.loans')
            if loans_cache:
                raw_loans: list[dict[str, ...]] = orjson.loads(loans_cache)
                loans = [LoanRead(**loan) for loan in raw_loans]
                return loans
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)

        db_loans: Sequence[Loan] = await loan_repo.get_all(email=email)
        loans = [LoanRead(**loan.__dict__) for loan in db_loans]
        data_loans: list[dict[str, ...]] = [loan.model_dump() for loan in loans]
        json_loans: bytes = orjson.dumps(data_loans, default=orjson_default)

        try:
            await cache.set(f'user:{email}.loans', json_loans, ex=settings.cache.ttl)
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)
        return loans

    @staticmethod
    async def get_loan(session: AsyncSession, loan_id: UUID, email: str) -> LoanRead:
        loan_repo: LoanRepository = LoanRepository(session=session)
        loan: LoanRead | None = None
        try:
            cache_loan: bytes | None = await cache.get(f'user:{email}.loan:{loan_id}')
            if cache_loan:
                loan_dict: dict[str, ...] = orjson.loads(cache_loan)
                loan = LoanRead(**loan_dict)
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)
        if not loan:
            loan_db: Loan | None = await loan_repo.get(id=loan_id, email=email)
            loan = LoanRead(**loan_db.__dict__)
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
        try:
            await cache.delete(f'user:{email}.loan:{loan_id}')
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)
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
