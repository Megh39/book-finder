$ErrorActionPreference = "Stop"

Write-Host "=== BOOK-FINDER: FULL PIPELINE (Windows) ==="

# Activate venv if exists
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "[1/8] Activating venv..."
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "WARNING: .venv not found. Running with global Python."
}

# Install deps (optional but safe)
Write-Host "[2/8] Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Playwright browser (only chromium is enough)
Write-Host "[3/8] Installing Playwright browser (chromium)..."
playwright install chromium

# ---- INGESTION ----
Write-Host "[4/8] Koha OPAC scraping..."
python ingestion/opac_data_scraper.py

Write-Host "[5/8] OpenLibrary enrichment..."
python ingestion/openlibrary_data_collector.py

Write-Host "[6/8] OpenAlex enrichment..."
python ingestion/openalex_data_collector.py

# ---- TRANSFORMATION ----
Write-Host "[7/8] Building final dataset..."
python transformation/build_final_dataset.py

Write-Host "[8/8] Final dataset transformation..."
python transformation/final_dataset_transformation.py

# ---- STORAGE ----
Write-Host "Creating DB..."
python storage/db_create.py

Write-Host "Loading DB..."
python storage/db_books_load.py

# ---- SERVE ----
Write-Host "Starting FastAPI server..."
python -m uvicorn api.main:app --reload
