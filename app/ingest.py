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
#------------------------------------------#

def strip_html():
    #use default BeautifulSoup behaviour to strip html
    return " ".join(
        BeautifulSoup(text or "", "lxml").get_text(" ", strip=True).split()
    )

def insert_batch(rows: List[RegInsight])
    #inserts multiple RegInsight objects at once into PostGresSQL (PG) DB

    sql = """INSERT INTO reginsights_clean
        (doc_id, jurisdiction, ontology_id, bucket_7d,
         published_date, title, clean_text, embedding)
      VALUES %s
      ON CONFLICT (doc_id) DO NOTHING;
    """
    values = [
        (
            r.doc_id,
            r.jurisdiction,
            r.ontology_id,
            week_bucket(r.published_date),
            r.published_date.date(),
            r.title,
            r.text_native,
            None,                   # embedding placeholder
        )
        for r in rows
    ]

    with db_conn() as conn, conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values)

def main():
    #Loads and cleans batches of data into the PG table

    #configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    kept = 0
    skipped = 0

    batch = list[RegInsight] = []

    
