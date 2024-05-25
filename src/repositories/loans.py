from typing import Sequence

from sqlalchemy import select, ScalarResult
from src.database.models.loans import Loan
from .sqlalchemy_repository import SqlAlchemyRepository
from ..database.models import User


class LoanRepository(SqlAlchemyRepository[Loan]):
    model = Loan

    async def get_all(self, **kwargs) -> Sequence[Loan]:
        loans: ScalarResult = await self.session.scalars(
            select(Loan)
            .select_from(User)
            .join(Loan, Loan.user_id == User.id)
            .where(User.email == kwargs.get('email'))
        )
        return loans.all()
