"""
Serviço responsável por persistir mensagens
que foram enviadas para alguma Dead Letter Queue.

Centralizar isso facilita auditoria
e eventual reprocessamento.
"""

import json

from app.database import get_connection


async def save_dead_letter(source: str, payload: dict, error: str):

    async with get_connection() as conn:

        async with conn.cursor() as cur:

            await cur.execute(
                """
                INSERT INTO lead_dead_letter(
                    source,
                    payload,
                    error_message
                )
                VALUES(
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    source,
                    json.dumps(payload),
                    error,
                ),
            )

        await conn.commit()