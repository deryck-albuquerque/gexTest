-- 1. Lag médio entre transaction_time do gateway e delivered_at em SMS, agrupado por gateway, nas últimas 24h.
SELECT
    o.gateway,
    AVG(
        TIMESTAMPDIFF(
            SECOND,
            le.transaction_time,
            ds.delivered_at
        )
    ) AS avg_lag_seconds
FROM lead_events le
JOIN orders o
    ON o.id = le.order_id
JOIN distribution_status ds
    ON ds.order_id = o.id
WHERE
    le.event = 'order.approved'
    AND ds.channel = 'SMS'
    AND ds.status = 'delivered'
    AND ds.delivered_at >= UTC_TIMESTAMP() - INTERVAL 24 HOUR
GROUP BY
    o.gateway;


-- 2. Leads em pending há mais de 5 minutos.
SELECT
    ds.order_id,
    ds.channel,
    TIMESTAMPDIFF(
        SECOND,
        ds.created_at,
        UTC_TIMESTAMP()
    ) AS age_seconds
FROM distribution_status ds
WHERE
    ds.status = 'pending'
    AND ds.created_at < UTC_TIMESTAMP() - INTERVAL 5 MINUTE
ORDER BY
    age_seconds DESC;


-- 3. Taxa de sucesso de SMS por produto, por hora, nas últimas 6h.
SELECT
    DATE_FORMAT(ds.created_at, '%Y-%m-%d %H:00:00') AS hour_ref,
    o.product_name,
    COUNT(*) AS total_sms,
    SUM(
        CASE
            WHEN ds.status = 'delivered'
            THEN 1
            ELSE 0
        END
    ) AS delivered_sms,
    ROUND(
        SUM(
            CASE
                WHEN ds.status = 'delivered'
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS success_rate_percent
FROM distribution_status ds
JOIN orders o
    ON o.id = ds.order_id
WHERE
    ds.channel = 'SMS'
    AND ds.created_at >= UTC_TIMESTAMP() - INTERVAL 6 HOUR
GROUP BY
    hour_ref,
    o.product_name
ORDER BY
    hour_ref DESC,
    o.product_name;


-- 4. Quantos leads em DLQ por motivo, nas últimas 24h.
SELECT
    source,
    error_message,
    COUNT(*) AS total
FROM lead_dead_letter
WHERE
    created_at >= UTC_TIMESTAMP() - INTERVAL 24 HOUR
GROUP BY
    source,
    error_message
ORDER BY
    total DESC;


-- 5. Reconciliação: aprovados em lead_events vs delivered em SMS, por dia, últimos 7 dias.
SELECT
    DATE(le.persisted_at) AS day_ref,

    COUNT(DISTINCT le.id) AS approved,

    COUNT(DISTINCT CASE
        WHEN ds.channel = 'SMS'
         AND ds.status = 'delivered'
        THEN ds.id
    END) AS sms_delivered,

    COUNT(DISTINCT le.id)
    -
    COUNT(DISTINCT CASE
        WHEN ds.channel = 'SMS'
         AND ds.status = 'delivered'
        THEN ds.id
    END) AS absolute_gap,

    ROUND(
        (
            COUNT(DISTINCT le.id)
            -
            COUNT(DISTINCT CASE
                WHEN ds.channel = 'SMS'
                 AND ds.status = 'delivered'
                THEN ds.id
            END)
        ) * 100.0 / NULLIF(COUNT(DISTINCT le.id), 0),
        2
    ) AS gap_percent

FROM lead_events le
LEFT JOIN distribution_status ds
    ON ds.order_id = le.order_id
WHERE
    le.event = 'order.approved'
    AND le.persisted_at >= UTC_TIMESTAMP() - INTERVAL 7 DAY
GROUP BY
    DATE(le.persisted_at)
ORDER BY
    day_ref DESC;