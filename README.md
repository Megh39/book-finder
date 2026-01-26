# Book Finder Data Engineering Pipeline
**Name:** Megh  
**Roll No:** <YOUR_ROLL_NO>

A complete end-to-end data engineering project designed to collect book metadata from multiple sources, clean and transform it into a structured dataset, store it in a local SQLite database, and serve it through a FastAPI API for searching and retrieval.

This project is built to run on **Windows**, **Linux (Ubuntu)**, and **macOS**, using Python scripts and a modular pipeline approach.
---

## Features
* **Multi-Source Enrichment**
  * **Koha OPAC (DAIICT)** scraping using **Playwright** (handles security checks better than basic scrapers).
  * **OpenLibrary API** enrichment using multiple endpoints (Edition → Work → Author).
  * **OpenAlex API** enrichment using title-based search and similarity scoring.
* **Data Transformation**
  * Cleans descriptions and subjects.
  * Removes HTML noise and encoding artifacts.
  * Picks best final description/subjects across sources.
* **Persistent Storage**
  * Stores final processed dataset in a local **SQLite** database (`books.db`).
* **FastAPI Access**
  * REST API endpoints for searching by title, author, ISBN, subjects, description, and full-text match.
* **Resume-Safe Scraping**
  * Scripts save checkpoints and resume from the last completed state to avoid losing progress.
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
│   ├── koha_scraper.py           # Playwright scraper for OPAC Koha
│   ├── openlibrary_enricher.py   # OpenLibrary enrichment pipeline
│   └── openalex_enricher.py      # OpenAlex enrichment pipeline
├── transformation/
│   ├── build_final_dataset.py    # Merge Koha + OpenLibrary + OpenAlex
│   └── final_text_builder.py     # Builds final_description + final_subjects
├── storage/
│   ├── db_create.py              # Creates SQLite DB + books table
│   └── db_books_load.py          # Loads final dataset into SQLite
├── logs/
│   └── llm_usage.md              # LLM usage log (manual Q/A)
├── outputs/                      # Optional exports
├── README.md                     # Documentation
└── requirements.txt              # Dependencies

```md
---

## Installation & Setup

### 1. Prerequisites
* **Python 3.10+**
* Internet access (for OpenLibrary/OpenAlex + Koha OPAC scraping)
* Chromium browser (Playwright installs it automatically)

### 2. Create Virtual Environment

**Windows**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
