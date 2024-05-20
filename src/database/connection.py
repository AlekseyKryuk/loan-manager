from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from src.config import settings


engine = create_async_engine(
    url=settings.db.url,
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    max_overflow=settings.db.max_overflow,
    pool_size=settings.db.pool_size
)

session_maker = async_sessionmaker[AsyncSession](
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)
