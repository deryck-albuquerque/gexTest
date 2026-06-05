CREATE TABLE raw_payloads (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    correlation_id CHAR(36),

    gateway VARCHAR(20),

    headers JSON,

    body_original JSON,

    body_decrypted JSON,

    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE webhook_idempotency (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    transaction_id VARCHAR(100) NOT NULL,

    event VARCHAR(100) NOT NULL,

    UNIQUE(transaction_id, event)
);


CREATE TABLE leads (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    email VARCHAR(255) NOT NULL,

    first_name VARCHAR(100),

    last_name VARCHAR(100),

    phone VARCHAR(30),

    country CHAR(2),

    UNIQUE(email)
);


CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    lead_id BIGINT NOT NULL,

    gateway VARCHAR(20) NOT NULL,

    transaction_id VARCHAR(100) NOT NULL,

    product_id VARCHAR(100),

    product_name VARCHAR(255),

    product_niche VARCHAR(100),

    quantity INT,

    amount_usd DECIMAL(10,2),

    payment_method VARCHAR(50),

    FOREIGN KEY (lead_id)
        REFERENCES leads(id),

    UNIQUE(gateway, transaction_id)
);


CREATE TABLE lead_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    order_id BIGINT NOT NULL,

    gateway VARCHAR(20) NOT NULL,

    correlation_id CHAR(36),

    event VARCHAR(100),

    transaction_time DATETIME,

    persisted_at DATETIME,

    lag_seconds BIGINT,

    FOREIGN KEY (order_id)
        REFERENCES orders(id),

    UNIQUE(order_id, event)
);


CREATE TABLE distribution_status (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    order_id BIGINT NOT NULL,

    channel VARCHAR(20),

    status VARCHAR(20),

    created_at DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    delivered_at DATETIME NULL,

    lag_channel_seconds BIGINT NULL,

    FOREIGN KEY (order_id)
        REFERENCES orders(id),

    UNIQUE(order_id, channel)
);


CREATE TABLE lead_dead_letter (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(100),
    payload JSON,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);