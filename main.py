import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.routers import root_router


logging.basicConfig(
    level=settings.logging.level,
    datefmt=settings.logging.date_format,
    format=settings.logging.format
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router=root_router)
