import sqlite3
import pandas as pd
import sys

from src.config import DB_PATH, FINAL_MASTER_WITH_FINAL_TEXT_CSV

DB_FILE = DB_PATH
CSV_FILE = FINAL_MASTER_WITH_FINAL_TEXT_CSV

df = pd.read_csv(CSV_FILE, engine="python", on_bad_lines="skip")

keep = [
    "row_id",
    "ISBN",
    "Title",
    "Author/Editor",
    "Year",
    "Place & Publisher",
    "final_description",
    "final_subjects",
    "final_description_source",
    "final_subjects_source",
]
df = df[keep].copy()

df = df.rename(
    columns={
        "ISBN": "isbn",
        "Title": "title",
        "Author/Editor": "author",
        "Year": "year",
        "Place & Publisher": "publisher",
        "final_description": "description",
        "final_subjects": "subjects",
        "final_description_source": "description_source",
        "final_subjects_source": "subjects_source",
    }
)

df["row_id"] = pd.to_numeric(df["row_id"], errors="coerce")
df = df[df["row_id"].notna()].copy()
df["row_id"] = df["row_id"].astype(int)

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df.loc[(df["year"] < 1800) | (df["year"] > 2026), "year"] = None

df["title"] = df["title"].fillna("UNKNOWN_TITLE").astype(str)
df.loc[df["title"].str.strip() == "", "title"] = "UNKNOWN_TITLE"

df = df.where(pd.notna(df), None)

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("PRAGMA journal_mode=WAL;")

sql = """
INSERT INTO books (
    row_id, isbn, title, author, year, publisher,
    description, subjects, description_source, subjects_source
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(row_id) DO UPDATE SET
    isbn=excluded.isbn,
    title=excluded.title,
    author=excluded.author,
    year=excluded.year,
    publisher=excluded.publisher,
    description=excluded.description,
    subjects=excluded.subjects,
    description_source=excluded.description_source,
    subjects_source=excluded.subjects_source;
"""

rows = 0

for r in df.itertuples(index=False):
    cur.execute(
        sql,
        (
            r.row_id,
            r.isbn,
            r.title,
            r.author,
            int(r.year) if pd.notna(r.year) else None,
            r.publisher,
            r.description,
            r.subjects,
            r.description_source,
            r.subjects_source,
        ),
    )
    rows += 1

conn.commit()
cur.close()
conn.close()

print("Loaded rows into DB:", rows)
