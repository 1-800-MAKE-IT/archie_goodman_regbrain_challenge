#file created by chatgpt
import psycopg2, psycopg2.extras
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env in CWD
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PW = os.getenv("DB_PASS")

def db_conn():
    return psycopg2.connect(
        host="localhost", port=5432,
        dbname=DB_NAME, user=DB_USER, password=DB_PW
    )