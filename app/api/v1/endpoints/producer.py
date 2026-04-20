from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.models.schemas import MessageRequest, MessageResponse
from app.services.rabbitmq_service import RabbitMQService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_rabbitmq_service() -> RabbitMQService:
    from app.main import rabbitmq_service
    if not rabbitmq_service:
        raise HTTPException(status_code=503, detail="RabbitMQ service not available")
    return rabbitmq_service


@router.post("/send", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """发送消息到RabbitMQ队列"""
    try:
        rabbitmq = get_rabbitmq_service()
        message_id = rabbitmq.publish_message(request.operation, request.data)

        logger.info(f"Message sent: {message_id}, operation: {request.operation}")

        return MessageResponse(
            success=True,
            message_id=message_id,
            message="Message sent to queue successfully",
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))