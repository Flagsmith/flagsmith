export const getClickHouseSetupSql = (
  database: string,
): string => `CREATE DATABASE IF NOT EXISTS ${database};

CREATE TABLE IF NOT EXISTS ${database}.events
(
    environment_key      LowCardinality(String),
    event                LowCardinality(String),
    feature_name         LowCardinality(String),
    timestamp            DateTime64(3),
    collected_at         DateTime64(3),
    identifier           String,
    value                String                          CODEC(ZSTD(3)),
    traits               String                          CODEC(ZSTD(3)),
    metadata             String                          CODEC(ZSTD(3)),
    sdk_language         LowCardinality(String),
    sdk_version          LowCardinality(String),

    INDEX idx_identity identifier TYPE bloom_filter GRANULARITY 4,

    CONSTRAINT environment_key_not_empty CHECK environment_key != '',
    CONSTRAINT event_not_empty           CHECK event != '',
    CONSTRAINT timestamp_sane            CHECK timestamp > toDateTime64('2020-01-01 00:00:00', 3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (environment_key, event, feature_name, timestamp, identifier);`

export const getClickHouseOnboardingSql =
  (): string => `-- Create a dedicated user for Flagsmith
CREATE USER IF NOT EXISTS <USER>
    IDENTIFIED WITH sha256_password BY '<CHANGE_ME_PASSWORD>';

-- Allow it to write and read experiment events
GRANT SELECT, INSERT ON flagsmith_exp.events TO <USER>;

-- Allow it to check the events table exists
GRANT SHOW TABLES, SHOW COLUMNS ON flagsmith_exp.* TO <USER>;

-- Create the database and events table
${getClickHouseSetupSql('flagsmith_exp')}`
