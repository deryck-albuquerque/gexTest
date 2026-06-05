-- Busca e agrupamento por gateway
CREATE INDEX idx_orders_gateway
ON orders(gateway);

-- Taxa de sucesso por produto
CREATE INDEX idx_orders_product_name
ON orders(product_name);

-- Auditoria de eventos
CREATE INDEX idx_lead_events_event_persisted
ON lead_events(event, persisted_at);

-- Lag SMS
CREATE INDEX idx_distribution_channel_status_delivered
ON distribution_status(channel, status, delivered_at);

-- Pendências
CREATE INDEX idx_distribution_status_created
ON distribution_status(status, created_at);

-- DLQ
CREATE INDEX idx_dead_letter_source_created
ON lead_dead_letter(source, created_at);