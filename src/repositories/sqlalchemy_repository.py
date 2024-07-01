from typing import Mapping, Sequence

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from .abstract_repository import AbstractRepository
from src.database.models.base_model import Base


class SqlAlchemyRepository[Model: Base](AbstractRepository):
    model: Model

    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def create(self, **kwargs) -> Model:
        instance: Model = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, **kwargs) -> Model | None:
        entity: sqlalchemy.ScalarResult = await self.session.scalars(
            sqlalchemy
            .select(self.model)
            .filter_by(**kwargs)
        )
        return entity.one_or_none()

    async def update(self, data: Mapping[str, ...], **kwargs) -> Model | None:
        stmt = (
            sqlalchemy
            .update(self.model)
            .values(**data)
            .filter_by(**kwargs)
            .returning(self.model)
        )
        entity: sqlalchemy.ScalarResult = await self.session.scalars(stmt)
        return entity.one_or_none()

    async def delete(self, **kwargs) -> Model | None:
        stmt = (
            sqlalchemy
            .delete(self.model)
            .filter_by(**kwargs)
            .returning(self.model)
        )
        entity: sqlalchemy.ScalarResult = await self.session.scalars(stmt)
        return entity.one_or_none()

    async def create_many(
            self,
            entities: Sequence[Model]
    ) -> Sequence[Model]:
        self.session.add_all(entities)
        await self.session.flush()
        return entities
