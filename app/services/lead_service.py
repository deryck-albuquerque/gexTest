"""
Responsável por persistir a parte principal do lead.

Fluxo:
- chama a stored procedure sp_insert_lead
- procedure salva lead, order e lead_event em transação no MySQL

Toda lógica de banco do consumer fica centralizada aqui.
"""

from datetime import datetime, timezone

from app.database import get_connection


async def save_lead_pipeline(payload: dict, gateway: str, correlation_id: str):
    """
    Persiste os dados principais do lead no banco.

    A procedure sp_insert_lead faz:
    - upsert em leads
    - upsert em orders
    - insert em lead_events
    """

    # Data/hora original da venda enviada pelo gateway
    transaction_time = datetime.fromisoformat(payload["transaction_time"])

    # Momento atual no backend, em UTC
    now = datetime.now(timezone.utc)

    # Diferença entre a venda no gateway e o processamento no banco
    lag_seconds = int((now - transaction_time).total_seconds())

    async with get_connection() as conn:
        async with conn.cursor() as cur:

            # Chamada da stored procedure
            #
            # centraliza no MySQL a transação de:
            # - leads
            # - orders
            # - lead_events
            await cur.execute(
                """
                CALL sp_insert_lead(
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
                """,
                (
                    payload["customer"]["email"],
                    payload["customer"]["first_name"],
                    payload["customer"]["last_name"],
                    payload["customer"]["phone"],
                    payload["customer"]["country"],

                    gateway,
                    payload["transaction_id"],
                    payload["product"]["id"],
                    payload["product"]["name"],
                    payload["product"]["niche"],

                    payload["product"]["quantity"],
                    payload["payment"]["amount_usd"],
                    payload["payment"]["method"],

                    correlation_id,
                    payload["event"],

                    transaction_time.replace(tzinfo=None),

                    lag_seconds
                ),
            )

            # A procedure retorna:
            # SELECT v_order_id AS order_id, p_lag_seconds AS lag_seconds;
            result = await cur.fetchone()

            order_id = result[0]

            # Criação dos status dos canais
            channels = ["SMS", "EMAIL", "CALL_CENTER", "WHATSAPP"]

            for channel in channels:
                await cur.execute(
                    """
                    INSERT IGNORE INTO distribution_status(
                        order_id,
                        channel,
                        status
                    )
                    VALUES(
                        %s,
                        %s,
                        'pending'
                    )
                    """,
                    (
                        order_id,
                        channel,
                    ),
                )

        await conn.commit()

    return {"order_id": order_id, "lag_seconds": lag_seconds}