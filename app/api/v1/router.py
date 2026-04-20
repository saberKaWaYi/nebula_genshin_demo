from fastapi import APIRouter
from app.api.v1.endpoints import producer, consumer

api_router = APIRouter()

api_router.include_router(producer.router, prefix="/messages", tags=["messages"])
api_router.include_router(consumer.router, prefix="/messages", tags=["messages"])