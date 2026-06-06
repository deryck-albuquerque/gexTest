"""
Distribuidor SMS.

Responsável por:
1. Consumir fila dist.sms
2. Enviar para provider/mock SMS
3. Simular falha controlada
4. Retry exponencial
5. Atualizar distribution_status
6. Calcular lag DB -> canal
7. Enviar para DLQ após falha definitiva
"""

import asyncio
import json
import random

from datetime import datetime, timezone

import aiohttp
import aio_pika

from app.database import get_connection
from app.rabbit.connection import get_channel
from app.rabbit.publisher import publish
from app.services.dlq_service import save_dead_letter
from app.config import SMS_WEBHOOK_URL, SMS_FAILURE_RATE, DLQ_DIST_SMS_DEAD
from app.logging_config import logger
from app.metrics import sms_delivered_total


def get_log_context(data: dict) -> dict:
    payload = data.get("payload", {})

    return {
        "correlation_id": data.get("correlation_id"),
        "gateway": data.get("gateway"),
        "event": data.get("event") or payload.get("event"),
        "order_id": data.get("order_id"),
    }


async def send_sms(payload: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(SMS_WEBHOOK_URL, json=payload) as response:
            if response.status >= 400:
                raise Exception(f"sms_provider_error_{response.status}")


async def mark_sms_delivered(order_id: int):
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT created_at
                FROM distribution_status
                WHERE order_id = %s
                AND channel = 'SMS'
                LIMIT 1
                """,
                (order_id,),
            )

            row = await cur.fetchone()
            lag_seconds = None

            if row:
                created_at = row[0].replace(tzinfo=timezone.utc)

                lag_seconds = int(
                    (datetime.now(timezone.utc) - created_at).total_seconds()
                )

            await cur.execute(
                """
                UPDATE distribution_status
                SET
                    status = 'delivered',
                    delivered_at = UTC_TIMESTAMP(),
                    lag_channel_seconds = %s
                WHERE order_id = %s
                AND channel = 'SMS'
                """,
                (
                    lag_seconds,
                    order_id,
                ),
            )

        await conn.commit()

    return lag_seconds


async def mark_sms_failed(order_id: int):
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE distribution_status
                SET
                    status = 'failed',
                    delivered_at = NULL
                WHERE order_id = %s
                AND channel = 'SMS'
                """,
                (order_id,),
            )

        await conn.commit()


async def process_sms_payload(data: dict):
    payload = data["payload"]
    order_id = data["order_id"]

    log_context = get_log_context(data)

    if random.random() < SMS_FAILURE_RATE:
        raise Exception("random_sms_failure")

    await send_sms(payload)

    lag_seconds = await mark_sms_delivered(order_id)

    logger.info(
        "sms_delivered",
        extra={
            **log_context,
            "lag_seconds": lag_seconds,
        },
    )

    sms_delivered_total.labels(status="delivered").inc()


async def process_with_retry(data: dict):
    delays = [1, 4, 16]
    log_context = get_log_context(data)

    for attempt, delay in enumerate(delays, start=1):
        try:
            await process_sms_payload(data)
            return

        except Exception as e:
            logger.error("sms_retry",
                extra={
                    **log_context,
                    "attempt": attempt,
                    "error": str(e)
                },
            )

            if attempt < len(delays):
                await asyncio.sleep(delay)
                continue

            await mark_sms_failed(data["order_id"])

            await save_dead_letter(
                source=DLQ_DIST_SMS_DEAD,
                payload=data,
                error=str(e),
            )

            await publish(DLQ_DIST_SMS_DEAD,
                {
                    **log_context,
                    "error": str(e),
                    "payload": data
                },
            )

            logger.error("sms_sent_to_dlq",
                extra={
                    **log_context,
                    "error": str(e)
                },
            )

            sms_delivered_total.labels(status="failed").inc()


async def process_sms_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        await process_with_retry(data)


async def start_sms_worker():
    channel = await get_channel()

    queue = await channel.declare_queue("dist.sms", durable=True)

    await queue.consume(process_sms_message)

    logger.info("sms_worker_started",
        extra={
            "correlation_id": None,
            "gateway": None,
            "event": None,
            "sms_failure_rate": SMS_FAILURE_RATE,
            "sms_webhook_url": SMS_WEBHOOK_URL
        },
    )

    await asyncio.Future()