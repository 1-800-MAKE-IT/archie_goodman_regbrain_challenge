"""
This script ingests data from RegInsight data CSV file, cleans data and inserts into PG table.
"""

from __future__ import annotations
import csv
import logging
from pathlib import Path
from typing import List, Generator
from datetime import datetime, timedelta
import psycopg2.extras
from bs4 import BeautifulSoup
from app.models import RegInsight
from app.utils.db_utils import db_conn  # returns psycopg2 connection

# ------------ Global variables ------------ #
RAW_CSV = Path("/workspaces/archie_goodman_regbrain_challenge/data/RegInsight_Dataset(RegInsight Data).csv")
BATCH_SIZE: int = 200
MIN_CHARS: int = 500
# ---------------------------------------- #

def ten_day_bucket(date: datetime) -> str:
    """Calculate a 10-day bucket for a given date."""
    bucket_start = date - ((date.day - 1) % 10) * timedelta(days=1)
    bucket_end = bucket_start + timedelta(days=9)
    return f"{bucket_start.strftime('%Y-%m-%d')} to {bucket_end.strftime('%Y-%m-%d')}"

def strip_html(text: str) -> str:
    """Clean HTML content."""
    try:
        return " ".join(
            BeautifulSoup(text or "", "lxml").get_text(" ", strip=True).split()
        )
    except Exception as e:
        logging.warning(f"Error stripping HTML: {e}. Returning empty string.")
        return ""

def parse_date(date_str: str) -> datetime:
    """Parse date string in 'MM/DD/YYYY' format."""
    try:
        return datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        logging.warning(f"Invalid date format: {date_str}. Using default date.")
        return datetime(1970, 1, 1)  # Default fallback date

def insert_batch(rows: List[dict]):
    """Insert multiple rows into PostgreSQL."""
    sql = """INSERT INTO reginsights_clean
        (doc_id, jurisdiction, ontology_id, time_bucket,
         published_date, title, clean_text, embedding)
      VALUES %s
      ON CONFLICT (doc_id) DO UPDATE SET jurisdiction = EXCLUDED.jurisdiction, ontology_id = EXCLUDED.ontology_id, title = EXCLUDED.title, clean_text = EXCLUDED.clean_text;
    """
    values = [
        (
            r["doc_id"],
            r["jurisdiction"],
            r["ontology_id"],
            r["time_bucket"],
            r["published_date"],
            r["title"],
            r["clean_text"],
            None,  # Embedding placeholder
        )
        for r in rows
    ]

    with db_conn() as conn, conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values)

def read_csv_in_batches(file_path: Path, batch_size: int) -> Generator[List[dict], None, None]:
    """Read CSV file and yield rows in batches."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as csvfile:
        reader = csv.DictReader(csvfile)
        batch = []
        for row in reader:
            try:
                published_date = parse_date(row["CUBEPublishedDate"])
                clean_text = strip_html(row["RegInsightTextNative"])
                if len(clean_text) >= MIN_CHARS:
                    batch.append(
                        {
                            "doc_id": row["RegInsightDocumentId"],
                            "jurisdiction": row["CUBEJurisdiction"],
                            "ontology_id": row["RegOntologyId"],
                            "time_bucket": ten_day_bucket(published_date),
                            "published_date": published_date.date(),
                            "title": row["RegInsightTitleNative"],
                            "clean_text": clean_text,
                        }
                    )
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            except Exception as e:
                logging.warning(f"Error processing row: {row}. Skipping. Error: {e}")
        if batch:
            yield batch

def main():
    """Load and clean batches of data into the PostgreSQL table."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.info("Starting data ingestion.")

    try:
        total_kept = 0
        for batch in read_csv_in_batches(RAW_CSV, BATCH_SIZE):
            insert_batch(batch)
            total_kept += len(batch)
            logging.info(f"Inserted batch of {len(batch)} rows (total kept: {total_kept})")

        logging.info(f"Ingestion completed. Total rows kept: {total_kept}")

    except Exception as e:
        logging.exception(f"An unexpected error occurred during ingestion: {e}")

if __name__ == "__main__":
    main()