import os
import asyncpg

pool: asyncpg.Pool | None = None


async def connect_db():
    """Opens a connection pool to Postgres on startup."""
    global pool
    pool = await asyncpg.create_pool(
        dsn=os.environ.get("DATABASE_URL", "postgresql://ab:ab@localhost:5432/ab_platform"),
        min_size=2,
        max_size=10,
    )


async def disconnect_db():
    """Closes all connections on shutdown."""
    if pool:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    """Returns the shared connection pool."""
    return pool
