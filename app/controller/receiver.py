import json
import time

import fastapi
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.schemas import WebhookPayload
from app.services.decrypt import decrypt_grummer
from app.services.normalizer import normalize_email, normalize_phone, normalize_name
from app.services.idempotency import check_and_register
from app.services.raw_payload_service import create_raw_payload, update_decrypted_payload
from app.rabbit.publisher import publish
from app.config import QUEUE_LEAD_RECEIVED, DLQ_DECRYPT_FAILED, DLQ_SCHEMA_FAILED
from app.logging_config import logger
from app.middleware import correlation_id_ctx
from app.metrics import leads_received_total, webhook_errors_total, webhook_latency_seconds

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@router.post("/{gateway}")
async def receive_webhook(gateway: str, request: Request):
    start_time = time.time()
    correlation_id = correlation_id_ctx.get()

    json_request = await request.json()
    body = json_request["body"]
    headers = json_request.get("headers", {})

    raw_payload_id = None
    decrypted_payload = None

    try:
        raw_payload_id = await create_raw_payload(correlation_id=correlation_id, gateway=gateway, headers=headers,
                                                  body_original=body)

        encrypted_header = (headers.get("X-GR-Encrypted") or headers.get("x-gr-encrypted"))

        try:
            if gateway == "grummer" and encrypted_header == "true":
                plaintext = decrypt_grummer(body)
                decrypted_payload = json.loads(plaintext)
            else:
                decrypted_payload = body

        except Exception as e:
            await publish(
                DLQ_DECRYPT_FAILED,
                {
                    "correlation_id": correlation_id,
                    "gateway": gateway,
                    "error": str(e),
                    "payload": body,
                },
            )

            logger.error(
                "decrypt_failed",
                extra={
                    "correlation_id": correlation_id,
                    "gateway": gateway,
                    "error": str(e),
                },
            )

            # métrica para errors de decrypt em payloads grummer
            webhook_errors_total.labels(gateway=gateway, error_type="decrypt_failed").inc()

            return JSONResponse(status_code=400,
                content={
                    "status": "decrypt_failed",
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            )

        await update_decrypted_payload(raw_payload_id=raw_payload_id, decrypted_payload=decrypted_payload)

        try:
            payload = WebhookPayload.model_validate(decrypted_payload)

        except ValidationError as e:
            await publish(DLQ_SCHEMA_FAILED,
                {
                    "correlation_id": correlation_id,
                    "gateway": gateway,
                    "error": str(e),
                    "payload": decrypted_payload,
                },
            )

            logger.error("schema_validation_failed",
                extra={
                    "correlation_id": correlation_id,
                    "gateway": gateway,
                    "error": str(e),
                },
            )

            # métrica para errors de schema
            webhook_errors_total.labels(gateway=gateway, error_type="schema_validation_failed").inc()

            return {
                "status": "schema_failed",
                "correlation_id": correlation_id,
            }

        if not payload.customer.first_name:
            payload.customer.first_name = "Customer"

        email, email_valid = normalize_email(payload.customer.email)
        phone, phone_valid = normalize_phone(payload.customer.phone)

        payload.customer.email = email
        payload.customer.phone = phone
        payload.customer.first_name = normalize_name(payload.customer.first_name)

        # criar idempotency key e validar exists
        is_new = await check_and_register(payload.transaction_id, payload.event)

        if not is_new:
            logger.info("duplicate_webhook",
                extra={
                    "correlation_id": correlation_id,
                    "gateway": gateway,
                    "event": payload.event,
                    "transaction_id": payload.transaction_id,
                },
            )

            return JSONResponse(status_code=200,
                content={
                    "status": "duplicate",
                    "correlation_id": correlation_id,
                },
            )

        if payload.event != "order.approved" or payload.payment.status != "approved":
            logger.info("non_approved_discarded",
                extra={
                    "correlation_id": correlation_id,
                    "gateway": gateway,
                    "event": payload.event,
                },
            )

            return JSONResponse(status_code=200,
                content={
                    "status": "discarded",
                    "correlation_id": correlation_id,
                },
            )

        await publish(QUEUE_LEAD_RECEIVED,
            {
                "correlation_id": correlation_id,
                "gateway": gateway,
                "payload": payload.model_dump(mode="json"),
                "email_valid": email_valid,
                "phone_valid": phone_valid,
            },
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        logger.info("lead_received",
            extra={
                "correlation_id": correlation_id,
                "gateway": gateway,
                "event": payload.event,
                "latency_ms": latency_ms,
            },
        )

        # métrica para lead com sucesso
        leads_received_total.labels(gateway=gateway, event=payload.event).inc()

        webhook_latency_seconds.labels(gateway=gateway).observe(latency_ms / 1000)

        return JSONResponse(status_code=202,
            content={
                "status": "accepted",
                "correlation_id": correlation_id,
            },
        )

    except Exception as e:
        logger.exception("webhook_internal_error",
            extra={
                "correlation_id": correlation_id,
                "gateway": gateway,
                "error": str(e),
            },
        )

        # métrica para internal error
        webhook_errors_total.labels(gateway=gateway, error_type="internal_error",).inc()

        return JSONResponse(status_code=500,
            content={
                "status": "internal_error",
                "correlation_id": correlation_id,
                "error": str(e),
            },
        )