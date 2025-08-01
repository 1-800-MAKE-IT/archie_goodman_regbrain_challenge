"""
This script ingests data from RegInsight data CSV file, cleans data and inserts into PG table.
Chatgpt model used - GPT 4o
"""

from __future__ import annotations
import csv
import logging
from pathlib import Path
from typing import List, Generator
from datetime import datetime, timedelta
import psycopg2.extras
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from models import RegInsight
from utils.db_utils import db_conn  


# ------------ Global variables ------------ #
RAW_CSV = Path("/workspaces/archie_goodman_regbrain_challenge/data/RegInsight_Dataset(RegInsight Data).csv")
BATCH_SIZE: int = 200
MIN_CHARS: int = 500
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2') 
# ---------------------------------------- #
#this function was produced with help from chatgpt
def ten_day_bucket(date: datetime) -> str:
    """Calculate a 10-day bucket for a given date."""
    bucket_start = date - ((date.day - 1) % 10) * timedelta(days=1)
    bucket_end = bucket_start + timedelta(days=9)
    return f"{bucket_start.strftime('%Y-%m-%d')} to {bucket_end.strftime('%Y-%m-%d')}"

#this function was produced with help from chatgpt
def strip_html(text: str) -> str:
    """Clean HTML content."""
    try:
        return " ".join(
            BeautifulSoup(text or "", "lxml").get_text(" ", strip=True).split()
        )
    except Exception as e:
        logging.warning(f"Error stripping HTML: {e}. Returning empty string.")
        return ""

#this function produced with help from chatgpt
def extract_concept_names(ontology_id: str) -> str:
    """Extract concept names from ontology ID strings."""
    if not ontology_id:
        return ""
    
    # Split by pipe to get individual concepts
    concepts = ontology_id.split('|')
    
    # For each concept, extract the part after the underscore
    concept_names = []
    for concept in concepts:
        if '_' in concept:
            concept_names.append(concept.split('_', 1)[1])
    
    # Join with pipe separator for storage
    return '|'.join(concept_names)

def get_embedding(text: str) -> list:
    embedding = EMBEDDING_MODEL.encode(text)
    return embedding.tolist()

def parse_date(date_str: str) -> datetime:
    """Parse date string in 'MM/DD/YYYY' format."""
    return datetime.strptime(date_str, "%m/%d/%Y")

def insert_batch(rows: List[dict]):
    #inserts a batch or rows into pg table. if there's a conflict, it just overwrites for now. suitable for the MVP
    sql = """INSERT INTO reginsights_clean
    (doc_id, jurisdiction, ontology_id, concept_names, time_bucket,
     published_date, title, clean_text, embedding)
    VALUES %s
    ON CONFLICT (doc_id) DO UPDATE SET 
        jurisdiction = EXCLUDED.jurisdiction, 
        ontology_id = EXCLUDED.ontology_id,
        concept_names = EXCLUDED.concept_names,
        time_bucket = EXCLUDED.time_bucket,
        published_date = EXCLUDED.published_date, 
        title = EXCLUDED.title, 
        clean_text = EXCLUDED.clean_text,
        embedding = EXCLUDED.embedding;
    """
    values = [
        (
            r["doc_id"],
            r["jurisdiction"],
            r["ontology_id"],
            r["concept_names"], 
            r["time_bucket"],
            r["published_date"],
            r["title"],
            r["clean_text"],
            r["embedding"],
        )
        for r in rows
    ]

    with db_conn() as conn, conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values)

def read_csv_in_batches(file_path: Path, batch_size: int) -> Generator[List[dict], None, None]:
    #generator to read csv and yeild batches of rows
    with open(file_path, "r", encoding="latin1") as csvfile:  #latin1 is a very tolerant csv encoding - change in prod? 
        reader = csv.DictReader(csvfile)
        batch = []
        for row in reader:
            try:
                #first sort out dates
                published_date = parse_date(row["CUBEPublishedDate"])  
                row["CUBEPublishedDate"] = published_date.isoformat()  

                # call datamodel
                validated_row = RegInsight(**row)
                clean_text = strip_html(validated_row.text_native)
                
                #some rows have too little text after stripping html 
                if len(clean_text) >= MIN_CHARS:

                    embedding = get_embedding(clean_text)
                    
                    batch.append(
                        {
                            "doc_id": validated_row.doc_id,
                            "jurisdiction": validated_row.jurisdiction,
                            "ontology_id": validated_row.ontology_id,
                            "concept_names": extract_concept_names(validated_row.ontology_id),
                            "time_bucket": ten_day_bucket(published_date),
                            "published_date": published_date.date(),  # Use the parsed datetime object
                            "title": validated_row.title,
                            "clean_text": clean_text,
                            "embedding": embedding,
                        }
                    )
                    
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            except Exception as e:
                logging.warning(f"Error processing row: {row}. Skipping. Error: {e}")
                raise e

        if batch:
            yield batch

#this function produced with help from chatgpt
def run_ingest() -> None:
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
        raise e

if __name__ == "__main__":
    run_ingest()
