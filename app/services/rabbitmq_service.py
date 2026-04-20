import pika
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RabbitMQService:
    """RabbitMQ 消息队列服务"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        queue_name: str = "neo4j_operations",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.queue_name = queue_name
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

    def connect(self) -> None:
        """建立RabbitMQ连接"""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()

        self._channel.queue_declare(queue=self.queue_name, durable=True)
        logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")

    def disconnect(self) -> None:
        """关闭RabbitMQ连接"""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("RabbitMQ connection closed")

    def publish_message(self, operation: str, data: dict) -> str:
        """发布消息到队列"""
        message_id = str(uuid.uuid4())
        message = {
            "message_id": message_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "data": data,
        }

        if not self._channel:
            self.connect()

        self._channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=json.dumps(message, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                message_id=message_id,
            ),
        )

        logger.info(f"Published message {message_id} with operation {operation}")
        return message_id

    def consume_message(self, auto_ack: bool = False) -> Optional[dict]:
        """从队列消费一条消息"""
        if not self._channel:
            self.connect()

        method_frame, properties, body = self._channel.basic_get(
            queue=self.queue_name, auto_ack=auto_ack
        )

        if method_frame is None:
            return None

        message = json.loads(body.decode("utf-8"))
        message["delivery_tag"] = method_frame.delivery_tag
        return message

    def acknowledge_message(self, delivery_tag: int) -> None:
        """确认消息处理完成"""
        if self._channel:
            self._channel.basic_ack(delivery_tag=delivery_tag)
            logger.info(f"Acknowledged message with delivery_tag {delivery_tag}")

    def reject_message(self, delivery_tag: int, requeue: bool = True) -> None:
        """拒绝消息，可选择重新入队"""
        if self._channel:
            self._channel.basic_reject(delivery_tag=delivery_tag, requeue=requeue)
            logger.info(
                f"Rejected message with delivery_tag {delivery_tag}, requeue={requeue}"
            )