from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from models.schemas import MessageRequest, MessageResponse
from services.rabbitmq_service import RabbitMQService
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_rabbitmq_service() -> RabbitMQService:
    from app.main import rabbitmq_service
    if not rabbitmq_service:
        raise HTTPException(status_code=503, detail="RabbitMQ service not available")
    return rabbitmq_service


@router.post("/send_nebula", response_model=MessageResponse)
async def send_nebula_message(request: MessageRequest):
    """发送消息到 Nebula 队列"""
    return await _send_to_queue(request, settings.rabbitmq_queue_nebula)


@router.post("/send_mongo", response_model=MessageResponse)
async def send_mongo_message(request: MessageRequest):
    """发送消息到 Mongo 队列"""
    return await _send_to_queue(request, settings.rabbitmq_queue_mongo)


async def _send_to_queue(request: MessageRequest, queue_name: str) -> MessageResponse:
    try:
        rabbitmq = get_rabbitmq_service()
        message_id = rabbitmq.publish_message(
            request.operation, request.data, queue_name=queue_name
        )

        logger.info(
            "Message sent: %s, operation: %s, queue: %s",
            message_id,
            request.operation,
            queue_name,
        )

        return MessageResponse(
            success=True,
            message_id=message_id,
            message=f"Message sent to queue successfully: {queue_name}",
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))