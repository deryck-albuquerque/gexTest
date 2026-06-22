import aio_pika
from app.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD

_connection = None


async def get_connection():
    global _connection

    if _connection is None:
        _connection = await aio_pika.connect_robust(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASSWORD,
        )

    return _connection


async def get_channel():
    conn = await get_connection()
    return await conn.channel()