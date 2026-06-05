"""
Consumer principal da esteira.

Responsável por:

1. Consumir lead.received
2. Persistir lead/order/event
3. Criar distribution_status
4. Publicar eventos downstream
5. Retry exponencial
6. Enviar para DLQ em falha definitiva
"""

import asyncio

from app.rabbit.publisher import publish

from app.services.lead_service import save_lead_pipeline

from app.services.dlq_service import save_dead_letter

from app.config import DLQ_CONSUMER_FAILED, QUEUE_DIST_SMS, QUEUE_DIST_EMAIL, QUEUE_DIST_CALLCENTER, QUEUE_DIST_WHATSAPP

from app.logging_config import logger


class ConsumerError(Exception):
    """
    Exceção específica do consumer.
    """
    pass


async def process_message(message: dict):
    """
    Processa uma mensagem recebida da fila lead.received.
    """

    correlation_id = message["correlation_id"]

    gateway = message["gateway"]

    payload = message["payload"]

    try:

        # Persistência da esteira
        #
        # Salva:
        # - lead
        # - order
        # - lead_event
        # - distribution_status
        #
        # Também calcula lag_seconds
        result = await save_lead_pipeline(
            payload=payload,
            gateway=gateway,
            correlation_id=correlation_id,
        )

        order_id = result["order_id"]

        lag_seconds = result["lag_seconds"]

        # Publicação para canais downstream
        #
        # somente SMS implementado.
        #
        # Porém criar os eventos dos demais para refletir a arquitetura real pedida no teste.
        await publish(
            QUEUE_DIST_SMS,
            {
                "order_id": order_id,
                "correlation_id": correlation_id,
                "gateway": gateway,
                "payload": payload,
            },
        )

        await publish(
            QUEUE_DIST_EMAIL,
            {
                "order_id": order_id,
                "correlation_id": correlation_id,
                "gateway": gateway,
            },
        )

        await publish(
            QUEUE_DIST_CALLCENTER,
            {
                "order_id": order_id,
                "correlation_id": correlation_id,
                "gateway": gateway,
            },
        )

        await publish(
            QUEUE_DIST_WHATSAPP,
            {
                "order_id": order_id,
                "correlation_id": correlation_id,
                "gateway": gateway,
            },
        )


        # Log de sucesso
        logger.info(
            "consumer_processed",
            extra={
                "correlation_id": correlation_id,
                "gateway": gateway,
                "event": payload["event"],
                "order_id": order_id,
                "lag_seconds": lag_seconds,
            },
        )

    except Exception as e:

        raise ConsumerError(str(e))


async def process_with_retry(message: dict):
    """
    Retry exponencial exigido pelo desafio.

    Tentativas:

    1s
    4s
    16s

    Após a terceira falha:
    - persiste em lead_dead_letter
    - publica na DLQ RabbitMQ
    """

    delays = [1, 4, 16]

    for attempt, delay in enumerate(delays, start=1):

        try:

            await process_message(message)

            return

        except Exception as e:

            logger.error(
                "consumer_retry",
                extra={
                    "attempt": attempt,
                    "error": str(e),
                    "correlation_id": message.get(
                        "correlation_id"
                    ),
                },
            )

            # Ainda existem tentativas
            if attempt < len(delays):

                await asyncio.sleep(delay)

                continue

            # Falha definitiva
            #
            # 1. Salva em lead_dead_letter
            # 2. Publica em DLQ RabbitMQ
            await save_dead_letter(
                source=DLQ_CONSUMER_FAILED,
                payload=message,
                error=str(e),
            )

            await publish(
                DLQ_CONSUMER_FAILED,
                {
                    "error": str(e),
                    "payload": message,
                },
            )

            logger.error("consumer_sent_to_dlq",
                extra={
                    "correlation_id": message.get(
                        "correlation_id"
                    ),
                    "error": str(e),
                },
            )