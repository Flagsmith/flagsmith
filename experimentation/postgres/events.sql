-- PostgreSQL schema for experimentation events.
CREATE SCHEMA IF NOT EXISTS flagsmith_exp;

CREATE TABLE IF NOT EXISTS flagsmith_exp.events (
    environment_key TEXT NOT NULL,
    event           TEXT NOT NULL,
    feature_name    TEXT,
    timestamp       TIMESTAMPTZ NOT NULL,
    collected_at    TIMESTAMPTZ,
    identifier      TEXT NOT NULL,
    value           TEXT,
    traits          TEXT,
    metadata        TEXT,
    sdk_language    TEXT,
    sdk_version     TEXT
);

CREATE INDEX IF NOT EXISTS events_env_event_feature_ts ON flagsmith_exp.events (environment_key, event, feature_name, timestamp);
CREATE INDEX IF NOT EXISTS events_env_event_identifier_ts ON flagsmith_exp.events (environment_key, event, identifier, timestamp);
