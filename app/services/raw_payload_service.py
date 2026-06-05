"""
Serviço responsável pela persistência dos payloads brutos.

Requisito do teste:
Todo payload recebido deve ser salvo,
inclusive payload inválido, erro de schema
ou erro de decrypt.
"""

import json

from app.database import get_connection


async def create_raw_payload(correlation_id: str, gateway: str, headers: dict, body_original: dict) -> int:
    """
    Cria o registro inicial.

    Retorna o ID para atualização posterior.
    """

    query = """
        INSERT INTO raw_payloads (
            correlation_id,
            gateway,
            headers,
            body_original
        )
        VALUES (%s, %s, %s, %s)
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query,
                (
                    correlation_id,
                    gateway,
                    json.dumps(headers),
                    json.dumps(body_original)
                )
            )

            await conn.commit()

            return cur.lastrowid


async def update_decrypted_payload(raw_payload_id: int, decrypted_payload: dict):
    """
    Atualiza o body descriptografado.

    Mantém um único registro para auditoria.
    """

    query = """
        UPDATE raw_payloads
        SET body_decrypted = %s
        WHERE id = %s
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query,
                (
                    json.dumps(decrypted_payload),
                    raw_payload_id
                )
            )

            await conn.commit()