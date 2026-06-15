-- Events table: every user action tracked by the platform
-- MergeTree is ClickHouse's primary table engine — optimized for time-series inserts and aggregations
CREATE TABLE IF NOT EXISTS events (
    experiment_id   String,
    variant_id      String,
    user_id         String,
    event_type      String,
    timestamp       DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (experiment_id, timestamp);

-- Materialized view: pre-aggregates conversion counts per variant
-- This runs automatically whenever new rows land in the events table,
-- so result queries are instant instead of scanning raw events every time
CREATE MATERIALIZED VIEW IF NOT EXISTS conversion_counts_mv
ENGINE = SummingMergeTree()
ORDER BY (experiment_id, variant_id, event_type)
AS
SELECT
    experiment_id,
    variant_id,
    event_type,
    count() AS conversion_count
FROM events
GROUP BY experiment_id, variant_id, event_type;
