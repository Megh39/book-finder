import sqlite3
from src.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
SELECT description, subjects
FROM books
WHERE title LIKE "Mathematics for machine learning"
LIMIT 5
""")

for d, s in cur.fetchall():
    print("---- DESCRIPTION ----")
    print(d[-300:])
    print("---- SUBJECTS ----")
    print(s)
    print("\n")

conn.close()
