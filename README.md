BOOK FINDER – DATA ENGINEERING PIPELINE
======================================

Name: Megh Nanavati
Roll No: 202518018


PROJECT OVERVIEW
----------------
This project implements a complete end-to-end data engineering pipeline
to collect, enrich, clean, store, and serve book metadata from multiple
heterogeneous sources.

The pipeline integrates:
- Web scraping (Koha OPAC)
- Public APIs (OpenLibrary, OpenAlex)
- Data cleaning and transformation logic
- Relational storage (SQLite)
- REST-based access using FastAPI

The system is designed to be reproducible, modular, and runnable from
the repository root without manual path manipulation.


KEY FEATURES
------------
1. Multi-Source Data Enrichment
   - Koha OPAC (DAIICT) scraping using Playwright
   - OpenLibrary API enrichment using:
       ISBN → Edition → Work → Author hierarchy
   - OpenAlex API enrichment using:
       Title-based search and similarity filtering

2. Robust Data Transformation
   - HTML tag and noise removal
   - Encoding artifact correction (â€™, â€, etc.)
   - Normalization of subjects and descriptions
   - Selection of best description/subjects using
     a priority-based source ranking

3. Persistent Local Storage
   - Final cleaned dataset stored in SQLite (books.db)
   - Schema designed for efficient search and retrieval

4. FastAPI-Based Query Interface
   - REST endpoints for title, author, ISBN, subject,
     description, and combined search
   - Swagger UI for interactive exploration

5. Resume-Safe Scraping
   - Intermediate outputs stored at each stage
   - Scripts detect completed rows and resume execution
     without duplicating work


PIPELINE EXECUTION FLOW
-----------------------
The pipeline is organized into four logical stages:

1. Ingestion
   - Load base dataset (CSV)
   - Enrich using Koha OPAC scraping
   - Enrich using OpenLibrary API
   - Enrich using OpenAlex API

2. Transformation
   - Merge all enriched datasets
   - Clean and normalize text fields
   - Construct final_description and final_subjects
     along with source metadata

3. Storage
   - Create SQLite database and schema
   - Load final dataset into database

4. Serving
   - Expose stored data via FastAPI endpoints


PROJECT STRUCTURE
-----------------
book-finder/
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # Centralized paths and constants
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── opac_data_scraper.py
│   │   ├── openlibrary_data_collector.py
│   │   └── openalex_data_collector.py
│   │
│   ├── transformation/
│   │   ├── __init__.py
│   │   ├── build_final_dataset.py
│   │   └── final_dataset_transformation.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db_create.py
│   │   └── db_books_load.py
│   │
│   └── api/
│       ├── __init__.py
│       └── main.py                # FastAPI application
│
├── data/
│   ├── raw/
│   │   └── books_data.csv
│   ├── interim/
│   │   ├── koha_enriched.csv
│   │   ├── openlibrary_enriched.csv
│   │   └── openalex_enriched.csv
│   └── processed/
│       ├── FINAL_MASTER_DATASET.csv
│       └── FINAL_MASTER_WITH_FINAL_TEXT.csv
│
├── storage/
│   └── books.db                   # SQLite database
│
├── logs/
│   └── llm_usage.md
│
├── run_all.ps1
├── run_all.sh
├── requirements.txt
└── README.txt


INSTALLATION & SETUP
--------------------
Prerequisites:
- Python 3.10 or higher
- Internet access
- Chromium browser (installed by Playwright)

Virtual environment setup:

Windows:
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1

Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Install Playwright browser:
playwright install chromium


RUNNING THE PIPELINE
-------------------
IMPORTANT:
All commands must be executed from the repository root.
Scripts are executed as Python modules, not as standalone files.

Automated execution:

Windows:
powershell -ExecutionPolicy Bypass -File .\\run_all.ps1

Linux/macOS:
chmod +x run_all.sh
./run_all.sh


MANUAL PIPELINE STEPS
--------------------

Base dataset cleaning:
python -m src.ingestion.library_data_cleaner

Koha OPAC enrichment:
python -m src.ingestion.opac_data_scraper

OpenLibrary enrichment:
python -m src.ingestion.openlibrary_data_collector

OpenAlex enrichment:
python -m src.ingestion.openalex_data_collector

Merge datasets:
python -m src.transformation.build_final_dataset

Final text construction:
python -m src.transformation.final_dataset_transformation

Create database:
python -m src.storage.db_create

Load database:
python -m src.storage.db_books_load

Dataset statistics:
python -m src.analysis.dataset_stats

RUNNING THE API
---------------
python -m uvicorn src.api.main:app --reload

Swagger UI:
http://127.0.0.1:8000/docs


DATABASE SCHEMA (books table)
-----------------------------
row_id               INTEGER (Primary Key)
isbn                 TEXT
title                TEXT
author               TEXT
year                 INTEGER
publisher             TEXT
description           TEXT
subjects              TEXT
description_source    TEXT
subjects_source       TEXT


DATA TRANSFORMATION LOGIC
------------------------
Description Cleaning:
- HTML tag removal
- Encoding artifact correction
- Removal of placeholder text
- Preference-based source selection

Subject Cleaning:
- Semicolon-separated normalization
- Best non-empty source selected

Year Cleaning:
- Valid years restricted to 1800–2026
- Invalid values set to NULL


WHY PLAYWRIGHT WAS USED
----------------------
Koha OPAC employs dynamic rendering and bot-detection mechanisms.
Traditional HTTP-based scrapers often fail or are blocked.

Playwright executes a real browser session, allowing:
- JavaScript-rendered content access
- Page interaction
- Manual verification when required


LLM USAGE DISCLOSURE
--------------------
AI tools were used for:
- Debugging assistance
- Architectural reasoning
- Code review and refactoring suggestions

All AI-assisted interactions are documented in:
logs/llm_usage.md


FUTURE ENHANCEMENTS
-------------------
- Semantic search using embeddings
- Natural language queries such as:
  "a story about a lonely robot in space"
- Migration to PostgreSQL for scalability
- CI checks for pipeline integrity
