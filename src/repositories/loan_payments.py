from typing import Sequence

from sqlalchemy import ScalarResult, select, and_

from src.database.models.loan_payments import LoanPayment
from src.database.models.loans import Loan
from .sqlalchemy_repository import SqlAlchemyRepository
from ..database.models import User


class LoanPaymentRepository(SqlAlchemyRepository[LoanPayment]):
    model = LoanPayment

    async def get_many(self, **kwargs) -> Sequence[LoanPayment]:
        payments: ScalarResult = await self.session.scalars(
            select(LoanPayment)
            .select_from(LoanPayment)
            .join(Loan, Loan.id == LoanPayment.loan_id)
            .join(User, User.id == Loan.user_id)
            .where(
                and_(
                    User.email == kwargs.get('email'),
                    Loan.id == kwargs.get('loan_id')
                )
            )
            .order_by(LoanPayment.payment_date)
        )
        return payments.all()
