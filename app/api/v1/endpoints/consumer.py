from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.models.schemas import ConsumeResponse, ConsumedMessage, HealthResponse
from app.services.rabbitmq_service import RabbitMQService
from app.services.neo4j_service import Neo4jService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_rabbitmq_service() -> RabbitMQService:
    from app.main import rabbitmq_service
    if not rabbitmq_service:
        raise HTTPException(status_code=503, detail="RabbitMQ service not available")
    return rabbitmq_service


def get_neo4j_service() -> Neo4jService:
    from app.main import neo4j_service
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service not available")
    return neo4j_service


@router.get("/consume", response_model=ConsumeResponse)
async def consume_message():
    """从RabbitMQ消费消息并执行Neo4j操作"""
    rabbitmq = get_rabbitmq_service()
    neo4j = get_neo4j_service()

    try:
        message = rabbitmq.consume_message(auto_ack=False)

        if message is None:
            return ConsumeResponse(
                success=False, message=None, error="No messages available in queue"
            )

        delivery_tag = message.pop("delivery_tag", None)

        operation = message.get("operation")
        data = message.get("data", {})

        result = neo4j.execute_operation(operation, data)

        if delivery_tag:
            rabbitmq.acknowledge_message(delivery_tag)

        logger.info(f"Successfully processed message: {message.get('message_id')}")

        return ConsumeResponse(
            success=True,
            message=ConsumedMessage(
                message_id=message.get("message_id"),
                timestamp=datetime.fromisoformat(message.get("timestamp")),
                operation=operation,
                data=data,
                status="completed",
            ),
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        if "delivery_tag" in locals() and delivery_tag:
            rabbitmq.reject_message(delivery_tag, requeue=True)

        return ConsumeResponse(success=False, message=None, error=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    from app.main import neo4j_service, rabbitmq_service

    neo4j_connected = neo4j_service is not None and neo4j_service._driver is not None
    rabbitmq_connected = rabbitmq_service is not None and rabbitmq_service._connection is not None

    status = "healthy" if (neo4j_connected and rabbitmq_connected) else "degraded"

    return HealthResponse(
        status=status,
        neo4j_connected=neo4j_connected,
        rabbitmq_connected=rabbitmq_connected,
    )