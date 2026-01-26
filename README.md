Book Finder Project

A complete end-to-end pipeline that takes raw library book data, enriches it using multiple external sources (DA-IICT OPAC Koha, OpenLibrary, OpenAlex), cleans + merges everything into one master dataset, stores it in SQLite, and serves it through a FastAPI backend for searching.

============================================================
1. Project Goals
============================================================
This project solves a real problem:

Most library datasets only contain basic metadata like Title, Author, Publisher, Year, ISBN.
They do not contain enough descriptive text to support good search like:
- “a story about a lonely robot in space”
- “books about optimization and gradient descent”
- “data science books about clustering and NLP”

So the goal is to enrich the dataset with:
- book descriptions
- subjects / categories / concept tags
- clean searchable text

Then store it in a database and expose an API.

============================================================
2. Project Folder Structure
============================================================
book-finder/
│
├── api/
│   └── main.py
│
├── data/
│   ├── raw/
│   │   └── books data.csv
│   │
│   ├── interim/
│   │   ├── koha_enriched.csv
│   │   ├── openlibrary_enriched.csv
│   │   └── openalex_enriched.csv
│   │
│   ├── processed/
│   │   ├── updated_books_data.csv
│   │   ├── FINAL_MASTER_DATASET.csv
│   │   └── FINAL_MASTER_WITH_FINAL_TEXT.csv
│
├── ingestion/
│   ├── library_data_cleaner.py
│   ├── koha_scraper.py
│   ├── openlibrary_enricher.py
│   └── openalex_enricher.py
│
├── transformation/
│   ├── build_final_dataset.py
│   └── build_final_text.py
│
├── storage/
│   ├── create_db.py
│   ├── db_books_load.py
│   └── books.db
│
├── logs/
│   ├── llm_usage.md
│   └── (runtime logs)
│
├── outputs/
│   └── (optional exports)
│
├── .gitignore
└── README.md

============================================================
3. Data Flow (Pipeline Overview)
============================================================

Step 0: Raw Library Data
Input file (raw export):
data/raw/books data.csv

This file may contain:
- duplicate rows
- encoding issues
- bad lines

------------------------------------------------------------
Step 1: Clean + Deduplicate Base Dataset
------------------------------------------------------------
Script:
ingestion/library_data_cleaner.py

Output:
data/processed/updated_books_data.csv

Deduplication rule used:
- keep first row
- drop duplicates based on:
  ["Title", "Page(s)", "Year", "Author/Editor", "ISBN"]

------------------------------------------------------------
Step 2: Enrich Using OPAC (Koha)
------------------------------------------------------------
Script:
ingestion/koha_scraper.py

Input:
data/processed/updated_books_data.csv

Output:
data/interim/koha_enriched.csv

Koha enrichment gives:
- OPAC detail URL
- subjects
- summary/description

Important:
- Koha may block scraping (captcha / security check)
- Playwright is required (BeautifulSoup alone won’t work)

------------------------------------------------------------
Step 3: Enrich Using OpenLibrary
------------------------------------------------------------
Script:
ingestion/openlibrary_enricher.py

Input:
data/processed/updated_books_data.csv

Output:
data/interim/openlibrary_enriched.csv

OpenLibrary enrichment hits multiple endpoints:
- /isbn/{isbn}.json edition data
- /authors/{id}.json author names
- /works/{id}.json subjects + better description

------------------------------------------------------------
Step 4: Enrich Using OpenAlex
------------------------------------------------------------
Script:
ingestion/openalex_enricher.py

Input:
data/processed/updated_books_data.csv

Output:
data/interim/openalex_enriched.csv

OpenAlex does NOT work well with ISBN for this dataset.
So the search is done using:
- Title search
- similarity scoring
- accept/reject based on confidence threshold

Outputs include:
- abstract (reconstructed)
- concept tags
- match status

------------------------------------------------------------
Step 5: Merge All Enrichment Into One Master CSV
------------------------------------------------------------
Script:
transformation/build_final_dataset.py

Output:
data/processed/FINAL_MASTER_DATASET.csv

Merge logic:
- Koha merge using ISBN
- OpenLibrary merge using ISBN
- OpenAlex merge using normalized Title match

------------------------------------------------------------
Step 6: Build Final Clean Searchable Text Columns
------------------------------------------------------------
Script:
transformation/build_final_text.py

Output:
data/processed/FINAL_MASTER_WITH_FINAL_TEXT.csv

This step:
- cleans encoding issues (â€™, etc.)
- strips HTML tags
- removes noise like “Table of contents”
- chooses best description + subjects from multiple sources

Priority rules:

Description priority:
1. Koha OPAC summary/description
2. OpenLibrary description
3. OpenAlex abstract

Subjects priority:
1. Koha OPAC subjects
2. OpenLibrary subjects
3. OpenAlex concept tags

It also stores:
- final_description_source
- final_subjects_source

Example sources:
- koha_opac
- openlibrary
- openalex

------------------------------------------------------------
Step 7: Store in SQLite Database
------------------------------------------------------------
Scripts:
storage/create_db.py
storage/db_books_load.py

Database file:
storage/books.db

Main table:
books

Columns:
- row_id (primary key)
- isbn
- title
- author
- year
- publisher
- description
- subjects
- description_source
- subjects_source

------------------------------------------------------------
Step 8: Serve API with FastAPI
------------------------------------------------------------
File:
api/main.py

Run:
uvicorn api.main:app --reload

Docs:
http://127.0.0.1:8000/docs

============================================================
4. API Endpoints
============================================================

Base Endpoints:
- GET /            -> welcome message
- GET /health      -> status check

Books:
- GET /books?limit=1000
- GET /books/{row_id}

Search:
- GET /search/title?q=...
- GET /search/author?q=...
- GET /search/isbn?q=...
- GET /search/subjects?q=...
- GET /search/description?q=...
- GET /search/all?q=...

============================================================
5. Common Issues + Fixes
============================================================

5.1 UnicodeDecodeError when reading raw CSV
Cause:
- raw file is not UTF-8 encoded

Fix:
- use encoding latin1 or cp1252

5.2 OPAC scraping fails using BeautifulSoup/Scrapy
Cause:
- OPAC has security checks + dynamic pages

Fix:
- use Playwright with a real browser session

5.3 Koha output contains duplicates
Cause:
- multiple retries / reruns append rows again

Fix:
- dedupe Koha output by ISBN during merge OR keep “best row per ISBN”

5.4 OpenAlex mismatch when merging on row_id
Cause:
- row_id is artificially generated and can shift after deduplication

Fix:
- merge OpenAlex using normalized Title key

5.5 NaN year breaks SQLite load
Cause:
- pandas uses NaN, not None

Fix:
- use pd.notna(year) before int(year)

5.6 DB path breaks when running API
Cause:
- relative paths depend on where uvicorn is launched

Fix:
- compute DB path using __file__

<!-- ============================================================ -->
------------------------------------------------------------
6. Full Run Order (Exact Steps)
------------------------------------------------------------
<!-- ============================================================ -->
Run from project root:

Step 1: Clean base dataset
python ingestion/library_data_cleaner.py

Step 2: Koha enrichment
python ingestion/koha_scraper.py

Step 3: OpenLibrary enrichment
python ingestion/openlibrary_enricher.py

Step 4: OpenAlex enrichment
python ingestion/openalex_enricher.py

Step 5: Merge all into master dataset
python transformation/build_final_dataset.py

Step 6: Build final cleaned text fields
python transformation/build_final_text.py

Step 7: Create DB + load data
python storage/create_db.py
python storage/db_books_load.py

Step 8: Start API
uvicorn api.main:app --reload

============================================================
7. Final Outputs
============================================================

Clean dataset:
data/processed/FINAL_MASTER_WITH_FINAL_TEXT.csv

SQLite DB:
storage/books.db

API docs:
http://127.0.0.1:8000/docs

============================================================
8. Future Improvements
============================================================
Planned upgrades:
- semantic search using embeddings
- vector database or FAISS index
- better ranking and filtering
- caching and rate limiting
- frontend UI for search

============================================================
9. Author Notes
============================================================
This project was built with a focus on:
- reliability (resume support + checkpoints)
- data correctness (dedupe + cleaning)
- scalable enrichment workflow
- searchable dataset output
