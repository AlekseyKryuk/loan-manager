from typing import Sequence, override, Mapping

from sqlalchemy import select, delete, update, and_, ScalarResult
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
            .order_by(Loan.name)
        )
        return loans.all()

    @override
    async def get(self, **kwargs) -> Loan | None:
        loan: ScalarResult = await self.session.scalars(
            select(Loan)
            .select_from(Loan)
            .join(User, Loan.user_id == User.id)
            .where(
                and_(
                    User.email == kwargs.get('email'),
                    Loan.id == kwargs.get('id')
                )
            )
        )
        return loan.one_or_none()

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

    @override
    async def update(self, data: Mapping[str, ...], **kwargs) -> Loan | None:
        loan: ScalarResult = await self.session.scalars(
            update(Loan)
            .where(
                and_(
                    Loan.id == kwargs.get("id"),
                    Loan.user_id == (
                        select(User.id)
                        .select_from(User)
                        .where(User.email == kwargs.get('email'))
                    )
                )
            )
            .values(**data)
            .returning(Loan)
        )
        return loan.one_or_none()
