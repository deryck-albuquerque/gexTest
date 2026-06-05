"""
Conexão assíncrona com MySQL usando aiomysql.
"""
import aiomysql
from contextlib import asynccontextmanager
from typing import Optional
from app.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_POOL_SIZE

_pool: Optional[aiomysql.Pool] = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DATABASE,
            minsize=1,
            maxsize=MYSQL_POOL_SIZE,
            autocommit=False,
            charset="utf8mb4",
        )
    return _pool


@asynccontextmanager
async def get_connection():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_cursor(conn=None, dict_cursor=True):
    if conn is None:
        async with get_connection() as new_conn:
            cursor_class = aiomysql.DictCursor if dict_cursor else aiomysql.Cursor
            async with new_conn.cursor(cursor_class) as cur:
                yield cur
                await new_conn.commit()
    else:
        cursor_class = aiomysql.DictCursor if dict_cursor else aiomysql.Cursor
        async with conn.cursor(cursor_class) as cur:
            yield cur


async def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None