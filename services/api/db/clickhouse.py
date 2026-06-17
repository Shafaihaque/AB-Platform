import os
import clickhouse_connect

def get_clickhouse():
    """Opens a ClickHouse connection."""
    return clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
        port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
    )
