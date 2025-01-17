import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.config import settings
from src.database.connection import engine
from src.routers import root_router


logging.basicConfig(
    level=settings.logging.level,
    datefmt=settings.logging.date_format,
    format=settings.logging.format
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)

app.include_router(router=root_router)
