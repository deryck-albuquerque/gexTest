import uuid
import contextvars

from fastapi import Request

correlation_id_ctx = contextvars.ContextVar("correlation_id", default=None)


async def correlation_middleware(request: Request, call_next):

    correlation_id = str(uuid.uuid4())

    correlation_id_ctx.set(correlation_id)

    response = await call_next(request)

    response.headers["X-Correlation-Id"] = correlation_id

    return response