from contextlib import asynccontextmanager

from config import setup_logging, settings

setup_logging("web")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.rabbitmq_service import RabbitMQService
from app.api.v1.router import api_router

rabbitmq_service: RabbitMQService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global rabbitmq_service

    rabbitmq_service = RabbitMQService(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        username=settings.rabbitmq_username,
        password=settings.rabbitmq_password,
        queue_names=[
            settings.rabbitmq_queue_nebula,
            settings.rabbitmq_queue_mongo,
        ],
        default_queue_name=settings.rabbitmq_queue_nebula,
    )
    rabbitmq_service.connect()

    yield

    rabbitmq_service.disconnect()


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()