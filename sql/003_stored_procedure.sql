DELIMITER $$

CREATE PROCEDURE sp_insert_lead(
    IN p_email VARCHAR(255),
    IN p_first_name VARCHAR(100),
    IN p_last_name VARCHAR(100),
    IN p_phone VARCHAR(30),
    IN p_country VARCHAR(2),

    IN p_gateway VARCHAR(20),
    IN p_transaction_id VARCHAR(100),
    IN p_product_id VARCHAR(50),
    IN p_product_name VARCHAR(255),
    IN p_product_niche VARCHAR(100),
    IN p_quantity INT,
    IN p_amount_usd DECIMAL(10,2),
    IN p_payment_method VARCHAR(50),

    IN p_correlation_id CHAR(36),
    IN p_event VARCHAR(100),
    IN p_transaction_time DATETIME,
    IN p_lag_seconds BIGINT
)
BEGIN
    DECLARE v_lead_id BIGINT;
    DECLARE v_order_id BIGINT;

    START TRANSACTION;

    INSERT INTO leads(
        email,
        first_name,
        last_name,
        phone,
        country
    )
    VALUES(
        p_email,
        p_first_name,
        p_last_name,
        p_phone,
        p_country
    )
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id);

    SET v_lead_id = LAST_INSERT_ID();

    INSERT INTO orders(
        lead_id,
        gateway,
        transaction_id,
        product_id,
        product_name,
        product_niche,
        quantity,
        amount_usd,
        payment_method
    )
    VALUES(
        v_lead_id,
        p_gateway,
        p_transaction_id,
        p_product_id,
        p_product_name,
        p_product_niche,
        p_quantity,
        p_amount_usd,
        p_payment_method
    )
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id);

    SET v_order_id = LAST_INSERT_ID();

    INSERT INTO lead_events(
        order_id,
        gateway,
        correlation_id,
        event,
        transaction_time,
        persisted_at,
        lag_seconds
    )
    VALUES(
        v_order_id,
        p_gateway,
        p_correlation_id,
        p_event,
        p_transaction_time,
        UTC_TIMESTAMP(),
        p_lag_seconds
    );

    COMMIT;

    SELECT
        v_order_id AS order_id,
        p_lag_seconds AS lag_seconds;
END$$

DELIMITER ;