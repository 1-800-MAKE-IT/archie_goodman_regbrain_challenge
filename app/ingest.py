"""
This script ingests data from RegInsight data CSV file, cleans data and inserts into PG table.
"""

from __future__ import annotations
#------------ default library imports ------------#
import csv
import logging
from pathlib import Path
from typing import List
#------------ external imports ------------#
import psycopg2.extras
from bs4 import BeautifulSoup
#------------ internal imports ------------#
from api.models import RegInsight
from app.utils.time_utils import week_bucket
from app.utils.db_utils import db_conn   # returns psycopg2 connection

#------------ Global variables ------------#
RAW_CSV = Path("data/cube_data.csv")
BATCH_SIZE : int = 200
MIN_CHARS : int = 500
#----------------------------------------#

def strip_html(text: str) -> str:
    try:
        return " ".join(
            BeautifulSoup(text or "", "lxml").get_text(" ", strip=True).split()
        )
    except Exception as e:
        logging.warning(f"Error stripping HTML: {e}. Returning empty string.")
        return ""

def insert_batch(rows: List[RegInsight]):
    #inserts multiple RegInsight objects at once into PostGresSQL (PG) DB

    sql = """INSERT INTO reginsights_clean
        (doc_id, jurisdiction, ontology_id, bucket_7d,
         published_date, title, clean_text, embedding)
      VALUES %s
      ON CONFLICT (doc_id) DO UPDATE SET jurisdiction = EXCLUDED.jurisdiction, ontology_id = EXCLUDED.ontology_id, title = EXCLUDED.title, clean_text = EXCLUDED.clean_text;
    """
    values = [
        (
            r.doc_id,
            r.jurisdiction,
            r.ontology_id,
            week_bucket(r.published_date),
            r.published_date.date(),
            r.title,
            strip_html(r.text_native),   #clean html here
            None,                   # embedding placeholder - will be updated later by a different script
        )
        for r in rows
    ]

    with db_conn() as conn, conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values)


#Loads and cleans batches of data into the PG table
def main():
    #configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    kept = 0
    skipped = 0  
    batch: List[RegInsight] = []  

    logging.info("Starting data ingestion.")

    try:
        with open(RAW_CSV, "r", encoding="utf-8") as csvfile: 
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Validate against pydantic data model
                    reg_insight = RegInsight(**row)

                    # Filter short texts (it's already been cleaned of HTML in insert batch function)
                    if len(reg_insight.text_native) < MIN_CHARS:
                        logging.debug(f"Skipping short text (length: {len(strip_html(reg_insight.text_native))}, doc_id: {reg_insight.doc_id})")
                        skipped += 1
                        continue

                    batch.append(reg_insight)
                    kept += 1

                    if len(batch) >= BATCH_SIZE:
                        insert_batch(batch)
                        logging.info(f"Inserted batch of {len(batch)} rows (total kept: {kept}, skipped: {skipped})")
                        batch = []  #new  batch

                except ValueError as e:
                    logging.error(f"Validation error: {e} for row: {row}")
                    skipped += 1
                except Exception as e:
                    logging.exception(f"Unexpected error processing row: {row}. Error: {e}")
                    skipped += 1

        # add last rows from last batch if needed
        if batch:
            insert_batch(batch)
            logging.info(f"Inserted final batch of {len(batch)} rows (total kept: {kept}, skipped: {skipped})")

    except FileNotFoundError:
        logging.error(f"CSV file not found: {RAW_CSV}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during ingestion: {e}")
    finally:
        logging.info(f"Ingestion completed. Total rows kept: {kept}, total rows skipped: {skipped}")
