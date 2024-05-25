from typing import Sequence, override

from sqlalchemy import select, delete, and_, ScalarResult
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

    @override
    async def delete(self, **kwargs) -> Loan | None:
        loan: ScalarResult = await self.session.scalars(
            delete(Loan)
            .where(
                and_(
                    Loan.id == kwargs.get('id'),
                    Loan.user_id == (
                        select(User.id)
                        .select_from(User)
                        .where(User.email == kwargs.get('email'))
                    )
                )
            )
            .returning(Loan)
        )
        return loan.one_or_none()
