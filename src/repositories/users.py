from src.database.models.users import User
from .sqlalchemy_repository import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    model = User
