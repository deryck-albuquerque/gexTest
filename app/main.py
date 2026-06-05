import uvicorn
from fastapi import FastAPI, Response
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.database import close_pool
from app.controller.receiver import router
from app.middleware import correlation_middleware
from app.logging_config import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Aplicação inicializada >_<")
    yield
    print("Aplicação encerrada -_-")
    await close_pool()

def init_app() -> FastAPI:
    appGexTest = FastAPI(
        title="GexTest",
        description="Esteira de integração de webhooks para marketing de resposta direta",
        version="1.0.0",
        lifespan=lifespan
    )

    # Healthcheck para load balancers e monitoramento.
    @appGexTest.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "gex-test",
            "version": "1.0.0"
        }

    # Mock pra simular recebimento de sms
    @appGexTest.post("/mock/sms")
    async def mock_sms(payload: dict):
        logger.info(
            "mock_sms_received",
            extra={"payload": payload}
        )

        return {"status": "received"}

    # Endpoint de métricas do prometheus
    @appGexTest.get("/metrics")
    async def metrics():
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

    appGexTest.middleware("http")(correlation_middleware)

    # Rota principal
    appGexTest.include_router(router)

    return appGexTest

app = init_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)