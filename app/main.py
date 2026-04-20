from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.services.neo4j_service import Neo4jService
from app.services.rabbitmq_service import RabbitMQService
from app.api.v1.router import api_router
import logging

logging.basicConfig(level=logging.INFO)

neo4j_service: Neo4jService = None
rabbitmq_service: RabbitMQService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global neo4j_service, rabbitmq_service

    neo4j_service = Neo4jService(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
    )
    neo4j_service.connect()

    rabbitmq_service = RabbitMQService(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        username=settings.rabbitmq_username,
        password=settings.rabbitmq_password,
        queue_name=settings.rabbitmq_queue,
    )
    rabbitmq_service.connect()

    yield

    neo4j_service.close()
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