from src.database.models.loans import Loan
from .sqlalchemy_repository import SqlAlchemyRepository


class LoanRepository(SqlAlchemyRepository[Loan]):
    model = Loan
