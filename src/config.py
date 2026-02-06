from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", BASE_DIR / "storage"))
LOG_DIR = Path(os.environ.get("LOG_DIR", BASE_DIR / "logs"))

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

ORIGINAL_DATA_CSV = RAW_DIR / "books_data.csv"
UPDATED_BOOKS_CSV = DATA_DIR / "updated_books_data.csv"

KOHA_ENRICHED_CSV = INTERIM_DIR / "koha_enriched.csv"
OPENLIBRARY_ENRICHED_CSV = INTERIM_DIR / "openlibrary_enriched.csv"
OPENALEX_ENRICHED_CSV = INTERIM_DIR / "openalex_enriched.csv"

FINAL_MASTER_DATASET_CSV = PROCESSED_DIR / "FINAL_MASTER_WITH_FINAL_TEXT.csv"
FINAL_MASTER_DATASET_CSV_2 =  PROCESSED_DIR / "FINAL_MASTER_WITH_FINAL_TEXT_v2.csv"
DB_PATH = STORAGE_DIR / "books.db"
for d in [DATA_DIR, RAW_DIR, INTERIM_DIR, PROCESSED_DIR, STORAGE_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)
