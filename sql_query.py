import sqlite3

DB_PATH = "books.db"   # same path you use everywhere

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

query = """
SELECT COUNT(*)
FROM books
WHERE lower(title) LIKE '%cyberpunk%'
   OR lower(description) LIKE '%cyberpunk%'
   OR lower(subjects) LIKE '%cyberpunk%';
"""

cur.execute(query)
result = cur.fetchone()

print("Result:", result)

conn.close()
