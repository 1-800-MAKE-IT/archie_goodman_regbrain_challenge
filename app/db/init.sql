CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS reginsights_clean (
    doc_id           UUID PRIMARY KEY,
    jurisdiction     TEXT NOT NULL,
    ontology_id      TEXT NOT NULL,
    concept_names    TEXT,              -- New column for human-readable concepts
    time_bucket      TEXT NOT NULL,
    published_date   DATE NOT NULL,
    title            TEXT,
    clean_text       TEXT NOT NULL,
    embedding        VECTOR(384)              
);