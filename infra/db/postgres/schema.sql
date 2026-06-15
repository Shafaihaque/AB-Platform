-- Experiments table: one row per experiment
CREATE TABLE IF NOT EXISTS experiments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'draft',  -- draft | running | paused | stopped
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Variants table: each experiment has 2+ variants
-- traffic_weight is a percentage (e.g. 50 means 50% of traffic)
CREATE TABLE IF NOT EXISTS variants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id   UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    traffic_weight  INTEGER NOT NULL DEFAULT 50,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Metrics table: what events count as a conversion for an experiment
CREATE TABLE IF NOT EXISTS metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id   UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    event_type      TEXT NOT NULL  -- e.g. "click", "signup", "purchase"
);
