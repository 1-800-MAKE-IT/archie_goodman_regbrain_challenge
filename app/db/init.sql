-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Target table (no need to create database - it's already created by docker)
CREATE TABLE IF NOT EXISTS reginsights_clean (
    doc_id           UUID PRIMARY KEY,
    jurisdiction     TEXT NOT NULL,
    ontology_id      TEXT NOT NULL,
    time_bucket          TEXT NOT NULL,
    published_date   DATE NOT NULL,
    title            TEXT,
    clean_text       TEXT NOT NULL,
    embedding        VECTOR(384)              -- NULL until embed.py fills
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_topic_qtr ON reginsights_clean (ontology_id, time_bucket);
CREATE INDEX IF NOT EXISTS idx_null_embed ON reginsights_clean (embedding) WHERE embedding IS NULL;