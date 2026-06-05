from prometheus_client import Counter, Histogram, Gauge

# Total de leads aprovados, recebidos e aceitos para processamento
leads_received_total = Counter(
    "leads_received_total",
    "Total de leads recebidos pela API",
    ["gateway", "event"]
)

# Total de falhas no pipeline de entrada
# (schema inválido, decrypt, erros internos, etc.)
webhook_errors_total = Counter(
    "webhook_errors_total",
    "Total de erros no processamento de webhooks",
    ["gateway", "error_type"]
)

# Tempo total de processamento da request HTTP, desde o recebimento até a publicação na fila
webhook_latency_seconds = Histogram(
    "webhook_latency_seconds",
    "Latência da request de webhook em segundos",
    ["gateway"]
)

# Tempo entre a geração do evento no gateway (transaction_time) e seu processamento interno
# utilizado para monitorar atraso de ingestão
lead_lag_seconds = Histogram(
    "lead_lag_seconds",
    "Lag entre transaction_time do gateway e processamento interno",
    ["gateway"]
)

# Total de SMS processados pela camada de distribuição, separados entre sucesso e falha
sms_delivered_total = Counter(
    "sms_delivered_total",
    "Total de SMS entregues",
    ["status"]
)