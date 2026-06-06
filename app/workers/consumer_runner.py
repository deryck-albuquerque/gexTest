import json
import asyncio

from aio_pika import connect_robust
from aio_pika import IncomingMessage

from app.config import RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_HOST, QUEUE_LEAD_RECEIVED

from app.workers.consumer import process_with_retry
from app.logging_config import logger


async def on_message(message: IncomingMessage):

    async with message.process():

        body = json.loads(message.body.decode())

        await process_with_retry(body)


async def main():

    connection = await connect_robust(f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}/")

    channel = await connection.channel()

    queue = await channel.declare_queue(QUEUE_LEAD_RECEIVED, durable=True)

    await queue.consume(on_message)

    logger.info("consumer_started",
        extra={
            "queue": QUEUE_LEAD_RECEIVED
        },
    )

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())