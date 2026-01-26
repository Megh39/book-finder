$ErrorActionPreference = "Stop"

Write-Host "=== BOOK-FINDER: FULL PIPELINE (Windows) ==="

function Assert-Exists($Path, $Label) {
    if (!(Test-Path $Path)) {
        throw "Missing $Label -> $Path"
    }
}

# Prechecks
Assert-Exists ".\config.py" "config.py"
Assert-Exists ".\requirements.txt" "requirements.txt"
Assert-Exists ".\api\main.py" "api/main.py"
Assert-Exists ".\data\updated_books_data.csv" "data/updated_books_data.csv"

# Activate venv
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "[SETUP] Activating venv..."
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "WARNING: .venv not found. Running with global Python."
}

# Install deps
Write-Host "[SETUP] Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Playwright browser
Write-Host "[SETUP] Installing Playwright browser (chromium)..."
playwright install chromium

# Ensure root import works everywhere
$env:PYTHONPATH = $PSScriptRoot

# ---- INGESTION ----
Write-Host "[1/6] Koha OPAC scraping..."
python .\ingestion\opac_data_scraper.py

Write-Host "[2/6] OpenLibrary enrichment..."
python .\ingestion\openlibrary_data_collector.py

Write-Host "[3/6] OpenAlex enrichment..."
python .\ingestion\openalex_data_collector.py

# ---- TRANSFORMATION ----
Write-Host "[4/6] Building final dataset..."
python .\transformation\build_final_dataset.py

Write-Host "[5/6] Final dataset transformation..."
python .\transformation\final_dataset_transformation.py

# ---- STORAGE ----
Write-Host "[6/6] Creating DB..."
python .\storage\db_create.py

Write-Host "[6/6] Loading DB..."
python .\storage\db_books_load.py

# ---- SERVE ----
Write-Host "[API] Starting FastAPI server..."
python -m uvicorn api.main:app --reload
