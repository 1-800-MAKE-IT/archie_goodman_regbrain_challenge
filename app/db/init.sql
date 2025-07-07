-- script created with ChatGPT, from the input schema, as it's quite boilerplate
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- One database for everything
CREATE DATABASE regbrain;

\c regbrain

-- Target table
CREATE TABLE IF NOT EXISTS reginsights_clean (
    doc_id           UUID PRIMARY KEY,
    jurisdiction     TEXT NOT NULL,
    ontology_id      TEXT NOT NULL,
    quarter          TEXT NOT NULL,
    published_date   DATE NOT NULL,
    title            TEXT,
    clean_text       TEXT NOT NULL,
    embedding        VECTOR(384)              -- NULL until embed.py fills
);

CREATE INDEX IF NOT EXISTS idx_topic_qtr ON reginsights_clean (ontology_id, quarter);
CREATE INDEX IF NOT EXISTS idx_null_embed ON reginsights_clean (embedding);
