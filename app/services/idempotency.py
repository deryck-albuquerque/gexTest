from pymysql.err import IntegrityError

from app.database import get_connection


async def check_and_register(transaction_id: str, event: str):

    async with get_connection() as conn:

        async with conn.cursor() as cur:

            try:

                await cur.execute(
                    """
                    INSERT INTO webhook_idempotency
                    (
                        transaction_id,
                        event
                    )
                    VALUES
                    (%s,%s)
                    """,
                    (
                        transaction_id,
                        event
                    )
                )

                await conn.commit()

                return True

            except IntegrityError:

                await conn.rollback()

                return False