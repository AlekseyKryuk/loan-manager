from abc import ABC, abstractmethod
from typing import Mapping


class AbstractRepository(ABC):
    @abstractmethod
    async def create(self, **kwargs: dict[str, ...]):
        raise NotImplementedError

    @abstractmethod
    async def get(self, **kwargs: dict[str, ...]):
        raise NotImplementedError

    @abstractmethod
    async def update(self, data: Mapping[str, ...], **kwargs: dict[str, ...]):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, **kwargs: dict[str, ...]):
        raise NotImplementedError
