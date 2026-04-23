import logging
import time

from config import settings, setup_logging, get_business_space
from services.nebula_service import NebulaService
from services.rabbitmq_service import RabbitMQService

setup_logging("worker")
logger = logging.getLogger("worker.run")


class QueueWorker:
    """单 worker 多队列分发消费者。"""

    def __init__(self):
        self.space_name = get_business_space("genshin")
        self.nebula = NebulaService(
            host=settings.nebula_host,
            port=settings.nebula_port,
            username=settings.nebula_username,
            password=settings.nebula_password,
        )
        self.rabbitmq = RabbitMQService(
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
        self.queue_handlers = {
            settings.rabbitmq_queue_nebula: self._handle_nebula_message,
            settings.rabbitmq_queue_mongo: self._handle_mongo_message,
        }
        self.queue_poll_order = [
            settings.rabbitmq_queue_nebula,
            settings.rabbitmq_queue_mongo,
        ]

    def run_forever(self) -> None:
        logger.info("Starting queue worker, queues=%s", self.queue_poll_order)
        self.nebula.connect()
        self.rabbitmq.connect()
        try:
            while True:
                has_message = False
                for queue_name in self.queue_poll_order:
                    message = self.rabbitmq.consume_message(
                        auto_ack=False,
                        queue_name=queue_name,
                    )
                    if message is None:
                        continue
                    has_message = True
                    self._dispatch_message(queue_name, message)
                if not has_message:
                    time.sleep(1.0)
        finally:
            self.nebula.close()
            self.rabbitmq.disconnect()

    def _dispatch_message(self, queue_name: str, message: dict) -> None:
        handler = self.queue_handlers.get(queue_name)
        delivery_tag = message.get("delivery_tag")
        if handler is None:
            logger.warning(
                "No handler for queue=%s message_id=%s; rejecting",
                queue_name,
                message.get("message_id"),
            )
            if delivery_tag:
                self.rabbitmq.reject_message(delivery_tag, requeue=False)
            return
        try:
            handler(message)
            if delivery_tag:
                self.rabbitmq.acknowledge_message(delivery_tag)
        except Exception as exc:
            logger.exception(
                "Worker failed queue=%s message_id=%s: %s",
                queue_name,
                message.get("message_id"),
                exc,
            )
            if delivery_tag:
                self.rabbitmq.reject_message(delivery_tag, requeue=True)

    def _handle_nebula_message(self, message: dict) -> None:
        operation = message.get("operation")
        data = message.get("data", {})
        result = self.nebula.execute_operation(self.space_name, operation, data)
        logger.info(
            "Nebula processed message_id=%s operation=%s result=%s",
            message.get("message_id"),
            operation,
            result,
        )

    def _handle_mongo_message(self, message: dict) -> None:
        logger.info(
            "Mongo handler placeholder consumed message_id=%s operation=%s",
            message.get("message_id"),
            message.get("operation"),
        )


def run_worker() -> None:
    worker = QueueWorker()
    worker.run_forever()
