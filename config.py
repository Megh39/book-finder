from pathlib import Path

# Repo root = folder containing this config.py
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
STORAGE_DIR= BASE_DIR/"storage"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

ORIGINAL_DATA_CSV = RAW_DIR / "books_data.csv"

UPDATED_BOOKS_CSV = DATA_DIR / "updated_books_data.csv"

KOHA_ENRICHED_CSV = INTERIM_DIR / "koha_enriched.csv"
OPENLIBRARY_ENRICHED_CSV = INTERIM_DIR / "openlibrary_enriched.csv"
OPENALEX_ENRICHED_CSV = INTERIM_DIR / "openalex_enriched.csv"

FINAL_MASTER_DATASET_CSV = PROCESSED_DIR / "FINAL_MASTER_DATASET.csv"
FINAL_MASTER_WITH_FINAL_TEXT_CSV = PROCESSED_DIR / "FINAL_MASTER_WITH_FINAL_TEXT.csv"

DB_PATH = STORAGE_DIR / "books.db"
