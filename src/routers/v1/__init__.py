from fastapi import APIRouter
from .users import router as user_router
# from .loans import router as loan_router


v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(user_router)
# v1_router.include_router(loan_router)
