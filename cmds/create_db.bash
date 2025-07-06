# One-time schema init: pipe SQL into the running DB container
docker exec -i regbrain-db psql -U reguser -d regbrain <<'SQL'


CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS reginsights_clean (
    doc_id          UUID PRIMARY KEY,
    jurisdiction    TEXT    NOT NULL,
    ontology_id     TEXT    NOT NULL,
    bucket_7d       TEXT    NOT NULL,      -- weekly bucket (Monday yyyy-mm-dd)
    published_date  DATE    NOT NULL,
    title           TEXT,
    clean_text      TEXT    NOT NULL,
    embedding       VECTOR(384)            -- NULL until embed.py fills
);

CREATE INDEX IF NOT EXISTS idx_topic_week   ON reginsights_clean (ontology_id, bucket_7d);
CREATE INDEX IF NOT EXISTS idx_null_embed   ON reginsights_clean (embedding);
SQL