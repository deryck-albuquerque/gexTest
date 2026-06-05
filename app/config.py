"""
Configurações centralizadas da aplicação GEX Test.
Todas as variáveis de ambiente com defaults para desenvolvimento local.
"""
import os

# MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", "10"))

# RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

# Filas
QUEUE_LEAD_RECEIVED = "lead.received"
QUEUE_DIST_SMS = "dist.sms"
QUEUE_DIST_EMAIL = "dist.email"
QUEUE_DIST_CALLCENTER = "dist.callcenter"
QUEUE_DIST_WHATSAPP = "dist.whatsapp"
DLQ_DECRYPT_FAILED = "lead.dead.decrypt_failed"
DLQ_SCHEMA_FAILED = "lead.dead.schema_failed"
DLQ_CONSUMER_FAILED = "lead.dead.consumer_failed"
DLQ_DIST_SMS_DEAD = "dist.dead.sms"

# Grummer Secret
GRUMMER_SECRET_KEY = os.getenv("GRUMMER_SECRET_KEY")

# Distribuidor SMS (webhook.site)
SMS_WEBHOOK_URL = os.getenv("SMS_WEBHOOK_URL")
SMS_FAILURE_RATE = float(os.getenv("SMS_FAILURE_RATE", "0.10"))

# Retry
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BACKOFF_BASE = int(os.getenv("RETRY_BACKOFF_BASE", "1"))

# App
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")