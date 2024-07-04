import logging
from calendar import monthrange, isleap
from decimal import Decimal
from typing import Sequence
from datetime import date, timedelta
from uuid import UUID

import redis
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from orjson import orjson
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.connection import cache
from src.config import settings
from src.database.models import LoanPayment
from src.database.models.loans import Loan
from src.repositories.loans import LoanRepository
from src.repositories.loan_payments import LoanPaymentRepository
from src.schemas.loan_payments import LoanPaymentCreate, LoanPaymentRead
from src.utils.serialization import orjson_default


logger = logging.getLogger(__name__)


class LoanPaymentService:

    @staticmethod
    def _create_schedule(
            payments: list[LoanPaymentCreate],
            loan: Loan
    ) -> list[LoanPayment]:

        def get_next_date(actual_date: date) -> date:
            cur_month_days = monthrange(actual_date.year, actual_date.month)[1]
            next_date = actual_date + timedelta(days=cur_month_days)
            return next_date

        schedule: list[LoanPayment] = []

        rate = Decimal(loan.interest_rate_percent) / 100
        loan_term = loan.loan_term
        loan_amount = Decimal(loan.loan_amount)

        monthly_interest = rate / 12
        default_payment_amount = loan_amount * (
                monthly_interest * (1 + monthly_interest) ** loan_term) / (
                                         (1 + monthly_interest) ** loan_term - 1
                                 )
        default_payment_amount = round(default_payment_amount, 2)

        if payments:
            payments.sort(key=lambda x: x.payment_date)
            if loan.start_date > payments[0].payment_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='The date of payment can not be earlier than the date of creating the loan'
                )

        if len(payments) < loan_term:
            previous_date = loan.start_date
            for index in range(loan_term):
                try:
                    payment = payments[index]
                    if payment.payment_amount is None:
                        payment.payment_amount = default_payment_amount
                    previous_date = payment.payment_date
                except IndexError:
                    current_date = get_next_date(previous_date)
                    payments.append(
                        LoanPaymentCreate(payment_date=current_date, payment_amount=default_payment_amount)
                    )
                    previous_date = current_date

        elif len(payments) > loan_term:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='The quantity of given payments can not be greater than "loan_term" value of the loan'
            )

        previous_date = loan.start_date
        remaining_balance = loan_amount

        for payment_number, payment in enumerate(payments, 1):
            if remaining_balance == 0:
                break

            current_date = payment.payment_date
            payment_amount = payment.payment_amount
            incoming_balance = remaining_balance

            period_data = {
                "loan_id": loan.id,
                "payment_number": payment_number,
                "payment_date": current_date,
                "incoming_balance": incoming_balance,
            }

            # evaluate the part of the year for the interest amount calculation
            current_date_year_days = 366 if isleap(current_date.year) else 365
            if current_date.year != previous_date.year:
                previous_date_year_days = 366 if isleap(previous_date.year) else 365
                prev_year_part = Decimal(
                    monthrange(previous_date.year, previous_date.month)[1] - previous_date.day
                ) / previous_date_year_days

                cur_year_part = Decimal(current_date.day / current_date_year_days)
                year_part = prev_year_part + cur_year_part
            else:
                year_part = Decimal((current_date - previous_date).days) / current_date_year_days

            interest_amount = round(incoming_balance * rate * year_part, 2)

            if interest_amount > payment_amount:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"The amount of interest can not be greater than the payment amount."
                           f"The payment for the date {current_date} is {payment_amount}, while "
                           f"the amount of interest for this payment is {interest_amount}"
                )

            if (payment_amount > interest_amount + incoming_balance) or (payment_number == loan_term):
                payment_amount = interest_amount + incoming_balance

            principal_amount = payment_amount - interest_amount
            remaining_balance = incoming_balance - principal_amount

            period_data.update(
                {
                    "payment_amount": payment_amount,
                    "interest_amount": interest_amount,
                    "principal_amount": principal_amount,
                    "remaining_balance": remaining_balance,
                    "year_part": year_part,
                    "days_in_year": current_date_year_days
                }
            )
            schedule.append(LoanPayment(**period_data))
            previous_date = current_date
        return schedule

    @staticmethod
    async def create_schedule(
        session: AsyncSession,
        loan_id: UUID,
        email: str,
        payments: list[LoanPaymentCreate],
    ) -> list[LoanPaymentRead]:
        payment_repo: LoanPaymentRepository = LoanPaymentRepository(session=session)
        loan_repo: LoanRepository = LoanRepository(session=session)

        loan: Loan = await loan_repo.get(email=email, id=loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The loan with supplied ID doesn't exist"
            )

        # check if schedule for the loan already exists
        loan_payments: Sequence[LoanPayment] = await payment_repo.get_many(email=email, loan_id=loan_id)
        if loan_payments:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The schedule for the loan with supplied ID already exists"
            )

        schedule: list[LoanPayment] = LoanPaymentService._create_schedule(payments=payments, loan=loan)
        try:
            db_schedule: Sequence[LoanPayment] = await payment_repo.create_many(schedule)
        except IntegrityError as e:
            logger.exception(e.args)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='There are repetitions among the transmitted dates. Each payment date must be unique.',
            )
        await session.commit()

        # redis set key with schedule
        loan_schedule: list[LoanPaymentRead] = []
        raw_schedule: list[dict[str, ...]] = []
        for payment in db_schedule:
            payment_read: LoanPaymentRead = LoanPaymentRead(**payment.__dict__)
            loan_schedule.append(payment_read)
            raw_schedule.append(payment_read.model_dump())

        json_schedule: bytes = orjson.dumps(raw_schedule, default=orjson_default)
        try:
            await cache.set(f'user:{email}.loan:{loan_id}.payments', json_schedule, ex=settings.cache.ttl)
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)
        return loan_schedule

    @staticmethod
    async def get_schedule(session: AsyncSession, loan_id: UUID, email: str) -> list[LoanPaymentRead]:
        try:
            cached_schedule: bytes = await cache.get(f'user:{email}.loan:{loan_id}.payments')
            if cached_schedule:
                raw_payments: list[dict[str, ...]] = orjson.loads(cached_schedule)
                loan_schedule = [LoanPaymentRead(**pay) for pay in raw_payments]
                return loan_schedule
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)

        payment_repo: LoanPaymentRepository = LoanPaymentRepository(session=session)
        loan_repo: LoanRepository = LoanRepository(session=session)

        loan: Loan = await loan_repo.get(email=email, id=loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The loan with supplied ID doesn't exist"
            )

        loan_payments: Sequence[LoanPayment] = await payment_repo.get_many(email=email, loan_id=loan_id)
        if not loan_payments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The schedule for the loan with supplied ID does not exist"
            )

        loan_schedule: list[LoanPaymentRead] = []
        raw_schedule: list[dict[str, ...]] = []
        for payment in loan_payments:
            payment_read: LoanPaymentRead = LoanPaymentRead(**payment.__dict__)
            loan_schedule.append(payment_read)
            raw_schedule.append(payment_read.model_dump())

        json_schedule: bytes = orjson.dumps(raw_schedule, default=orjson_default)
        try:
            await cache.set(f'user:{email}.loan:{loan_id}.payments', json_schedule, ex=settings.cache.ttl)
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)
        return loan_schedule

    @staticmethod
    async def delete_schedule(
            loan_id: UUID,
            email: str,
            session: AsyncSession,
    ) -> None:
        try:
            await cache.delete(f'user:{email}.loan:{loan_id}.payments')
        except redis.exceptions.ConnectionError as e:
            logger.exception(e.args)

        loan_repo: LoanRepository = LoanRepository(session=session)
        loan: Loan = await loan_repo.get(email=email, id=loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The loan with supplied ID doesn't exist"
            )
        payment_repo: LoanPaymentRepository = LoanPaymentRepository(session=session)
        deleted_payments: Sequence[LoanPayment] = await payment_repo.delete_many(loan_id=loan_id)
        if not deleted_payments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The schedule for the loan with supplied ID does not exist"
            )
