import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import DB_PATH
DB_FILE = DB_PATH

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS books (
    row_id INTEGER PRIMARY KEY,
    isbn TEXT,
    title TEXT NOT NULL,
    author TEXT,
    year TEXT,
    publisher TEXT,
    description TEXT,
    subjects TEXT,
    description_source TEXT,
    subjects_source TEXT
)
""")

conn.commit()
conn.close()

print("Created DB:", DB_FILE)
print("Created table: books")
