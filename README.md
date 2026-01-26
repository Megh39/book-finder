# Book Finder Data Engineering Pipeline
**Name:** Megh Nanavati
**Roll No:** 202518018

A complete end-to-end data engineering project designed to collect book metadata from multiple sources, clean and transform it into a structured dataset, store it in a local SQLite database, and serve it through a FastAPI API for searching and retrieval.

This project is built to run on **Windows**, **Linux (Ubuntu)**, and **macOS**, using Python scripts and a modular pipeline approach.

---

## Features
- **Multi-Source Enrichment**
  - **Koha OPAC (DAIICT)** scraping using **Playwright** (handles security checks better than basic scrapers).
  - **OpenLibrary API** enrichment using multiple endpoints (Edition → Work → Author).
  - **OpenAlex API** enrichment using title-based search and similarity scoring.
- **Data Transformation**
  - Cleans descriptions and subjects.
  - Removes HTML noise and encoding artifacts.
  - Picks best final description/subjects across sources.
- **Persistent Storage**
  - Stores final processed dataset in a local **SQLite** database (`books.db`).
- **FastAPI Access**
  - REST API endpoints for searching by title, author, ISBN, subjects, description, and full-text match.
- **Resume-Safe Scraping**
  - Scripts save checkpoints and resume from the last completed state to avoid losing progress.

---

## Pipeline Execution Flow
The project is structured into four main stages:

- **Ingestion**
  - Load base dataset (CSV of books).
  - Enrich using Koha OPAC scraping (ISBN search).
  - Enrich using OpenLibrary API (ISBN → edition/work/author).
  - Enrich using OpenAlex API (title search + similarity filtering).

- **Transformation**
  - Merge all sources into a master dataset.
  - Clean and normalize text fields.
  - Create final fields (`final_description`, `final_subjects`) with source tracking.

- **Storage**
  - Load cleaned dataset into SQLite database (`books.db`).

- **Serving**
  - FastAPI app serves the stored data for queries/search.

---

## Project Structure
```text
book-finder/
├── api/                          # FastAPI server
│   └── main.py                   # API endpoints (books, search)
├── data/
│   ├── raw/                      # Raw input files
│   │   └── books data.csv
│   ├── interim/                  # Enrichment outputs
│   │   ├── koha_enriched.csv
│   │   ├── openlibrary_enriched.csv
│   │   └── openalex_enriched.csv
│   └── processed/                # Final merged datasets
│       ├── FINAL_MASTER_DATASET.csv
│       └── FINAL_MASTER_WITH_FINAL_TEXT.csv
├── ingestion/
│   ├── opac_data_scraper.py           # Playwright scraper for OPAC Koha
│   ├── openlibary_data_collector.py   # OpenLibrary enrichment pipeline
│   └── openalex_data_collector.py      # OpenAlex enrichment pipeline
├── transformation/
│   ├── build_final_dataset.py    # Merge Koha + OpenLibrary + OpenAlex
│   └── final_dataset_transformation.py     # Builds final_description + final_subjects
├── storage/
│   ├── db_create.py              # Creates SQLite DB + books table
│   └── db_books_load.py          # Loads final dataset into SQLite
├── logs/
│   └── llm_usage.md              # LLM usage log (manual Q/A)
├── README.md                     # Documentation
└── requirements.txt              # Dependencies
```

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.10+**
- Internet access (for OpenLibrary/OpenAlex + Koha OPAC scraping)
- Chromium browser (Playwright installs it automatically)

### 2. Create Virtual Environment

#### Windows
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
```bash
playwright install
```

---

## Running the Pipeline

### Step A: Base Cleaning (Dedup)
Deduplicate base dataset rows by key columns:

```bash
python ingestion/library_data_cleaner.py
```

**Output:**
- `data/updated_books_data.csv`

---

### Step B: Koha OPAC Enrichment (Playwright Scraper)
Scrapes Koha OPAC using ISBN search and extracts:
- subjects
- summary/description
- detail page link
- status

```bash
python ingestion/opac_data_scraper.py
```

**Output:**
- `data/interim/koha_enriched.csv`

---

### Step C: OpenLibrary Enrichment (API)
Uses multiple OpenLibrary endpoints:
- `/isbn/{isbn}.json` (edition)
- `/works/{work}.json` (subjects + description fallback)
- `/authors/{author}.json` (author name)

```bash
python ingestion/openlibrary_data_collector.py
```

**Output:**
- `data/interim/openlibrary_enriched.csv`

---

### Step D: OpenAlex Enrichment (Title Search)
Since ISBN coverage is limited, OpenAlex enrichment is done using:
- Title search
- Similarity matching
- Status labels for acceptance/rejection

```bash
python ingestion/openalex_data_collector.py
```

**Output:**
- `data/interim/openalex_enriched.csv`

---

### Step E: Merge All Sources
Merge logic:
- Koha + OpenLibrary → join on ISBN
- OpenAlex → join on normalized Title key

```bash
python transformation/build_final_dataset.py
```

**Output:**
- `data/processed/FINAL_MASTER_DATASET.csv`

---

### Step F: Create Final Text Fields
Creates:
- `final_description`
- `final_subjects`
- `description_source`
- `subjects_source`

Priority order:
- Koha OPAC → OpenLibrary → OpenAlex

```bash
python transformation/final_dataset_transformation.py
```

**Output:**
- `data/processed/FINAL_MASTER_WITH_FINAL_TEXT.csv`

---

### Step G: Create Database + Load Data

Create DB + table:
```bash
python storage/db_create.py
```

Load final CSV into SQLite:
```bash
python storage/db_books_load.py
```

**Database:**
- `storage/books.db`

---

### Step H: Run FastAPI Server
```bash
uvicorn api.main:app --reload
```

---

## API Documentation
Once server is running:
- Swagger docs: `http://127.0.0.1:8000/docs`

### Available Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | GET | Welcome message |
| `/health` | GET | API health check |
| `/books` | GET | List books (limit controlled) |
| `/books/{row_id}` | GET | Get book by row_id |
| `/search/title?q=` | GET | Search by title |
| `/search/author?q=` | GET | Search by author |
| `/search/isbn?q=` | GET | Exact ISBN search |
| `/search/subjects?q=` | GET | Search by subjects |
| `/search/description?q=` | GET | Search by description |
| `/search/all?q=` | GET | Search across title/author/subjects/description |

---

## Data Dictionary (Books Table)

| Field | SQLite Type | Description |
| :--- | :--- | :--- |
| `row_id` | INTEGER | Primary key row identifier |
| `isbn` | TEXT | Book ISBN (normalized) |
| `title` | TEXT | Book title |
| `author` | TEXT | Author/Editor field |
| `year` | INTEGER | Publication year (cleaned range) |
| `publisher` | TEXT | Place & Publisher |
| `description` | TEXT | Final chosen description |
| `subjects` | TEXT | Final chosen subjects/tags |
| `description_source` | TEXT | Source label: `koha_opac`, `openlibrary`, `openalex` |
| `subjects_source` | TEXT | Source label: `koha_opac`, `openlibrary`, `openalex` |

---

## Data Transformation Logic

### Description Cleaning
- Removes HTML tags and `<br>`
- Fixes encoding artifacts like:
  - `â€™` → `'`
  - `â€”` → `-`
- Removes spam text like “Table of contents”
- Filters invalid placeholder descriptions (`nan`, `none`, `not available`)

### Subject Cleaning
- Uses semicolon-separated subjects/tags
- Picks best non-empty source field

### Year Cleaning
Some rows had invalid years like `0` or `2090`.

Fix applied:
- Keep only years between **1800 and 2026**
- Otherwise set year to `NULL`

---

## Why Playwright Was Needed for Koha OPAC
Koha OPAC sometimes shows:
- security check pages
- bot detection
- blocked requests

BeautifulSoup/Scrapy cannot solve that reliably because they only fetch static HTML without waiting or interacting.

Playwright works because it runs a real browser session and can handle manual verification when needed.

---

## LLM Usage Log
All AI-assisted decisions, debugging steps, and pipeline improvements are documented in:

- `logs/llm_usage.md`

Format:
- Question asked
- Answer given

---

## Common Issues & Fixes

### 1. Koha duplicates in output
**Cause:** multiple retries / manual reruns appended results  
**Fix:** dedupe based on ISBN or keep best row per ISBN during merge

### 2. OpenAlex mismatch when merging on row_id
**Cause:** base dataset did not have stable row_id  
**Fix:** merge OpenAlex using normalized title match instead

### 3. Resume scraping without losing progress
**Fix:**
- scripts store checkpoints every N rows
- scripts read existing output and skip completed rows

---

## Future Enhancements
- Add semantic search using embeddings for queries like: “a story about a lonely robot in space”
