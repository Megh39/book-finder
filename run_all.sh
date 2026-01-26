#!/usr/bin/env bash
set -e

echo "=== BOOK-FINDER: FULL PIPELINE (Linux/macOS) ==="

assert_exists () {
  if [ ! -f "$1" ]; then
    echo "Missing $2 -> $1"
    exit 1
  fi
}

# Prechecks
assert_exists "./config.py" "config.py"
assert_exists "./requirements.txt" "requirements.txt"
assert_exists "./api/main.py" "api/main.py"
assert_exists "./data/updated_books_data.csv" "data/updated_books_data.csv"

# Activate venv if exists
if [ -f ".venv/bin/activate" ]; then
  echo "[SETUP] Activating venv..."
  source .venv/bin/activate
else
  echo "WARNING: .venv not found. Running with global Python."
fi

# Install deps
echo "[SETUP] Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Playwright browser
echo "[SETUP] Installing Playwright browser (chromium)..."
playwright install chromium

# Ensure root import works everywhere
export PYTHONPATH="$(pwd)"

# ---- INGESTION ----
echo "[1/6] Koha OPAC scraping..."
python ./ingestion/opac_data_scraper.py

echo "[2/6] OpenLibrary enrichment..."
python ./ingestion/openlibrary_data_collector.py

echo "[3/6] OpenAlex enrichment..."
python ./ingestion/openalex_data_collector.py

# ---- TRANSFORMATION ----
echo "[4/6] Building final dataset..."
python ./transformation/build_final_dataset.py

echo "[5/6] Final dataset transformation..."
python ./transformation/final_dataset_transformation.py

# ---- STORAGE ----
echo "[6/6] Creating DB..."
python ./storage/db_create.py

echo "[6/6] Loading DB..."
python ./storage/db_books_load.py

# ---- SERVE ----
echo "[API] Starting FastAPI server..."
python -m uvicorn api.main:app --reload
