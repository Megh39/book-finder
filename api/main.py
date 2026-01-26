import sqlite3
from fastapi import FastAPI, HTTPException
import os,sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from config import DB_PATH

DB_FILE=DB_PATH
app = FastAPI(title="Book Finder API")


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def welcome():
    return {"message":"Welcome to Book Finder API! Please visit /docs for more info."}
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/books")
def books(limit: int = 1000):
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 5000")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
                SELECT row_id,isbn,title,author,year,publisher,description,
                subjects,description_source,subjects_source FROM books ORDER BY row_id ASC LIMIT ?""",
        (limit,),
    )
    row = [dict(r) for r in cur.fetchall()]
    conn.close()
    return row


@app.get("/books/{row_id}")
def search_by_row_id(row_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT row_id, isbn, title, author, year, publisher,
               description, subjects, description_source, subjects_source
        FROM books
        WHERE row_id = ?
    """,
        (row_id,),
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="book not found")

    return dict(row)


@app.get("/search/title")
def search_by_title(q: str, limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
                SELECT row_id, isbn, title, author, year, publisher,
                    description, subjects, description_source, subjects_source
                FROM books
                WHERE title LIKE ?
                LIMIT ?
                """,
        (f"%{q}%", limit),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="book not found")
    return [dict(r) for r in rows]


@app.get("/search/author")
def search_by_author(q: str, limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
                SELECT row_id, isbn, title, author, year, publisher,
                    description, subjects, description_source, subjects_source
                FROM books
                WHERE author LIKE ?
                LIMIT ?
                """,
        (f"%{q}%", limit),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="book not found")
    return [dict(r) for r in rows]


@app.get("/search/isbn")
def search_by_isbn(q: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
                SELECT row_id, isbn, title, author, year, publisher,
                    description, subjects, description_source, subjects_source
                FROM books
                WHERE isbn = ?
                LIMIT 1
                """,
        (q.strip(),),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="book not found")
    return dict(row)

@app.get("/search/subjects")
def search_by_subjects(q: str, limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
                SELECT row_id, isbn, title, author, year, publisher,
                    description, subjects, description_source, subjects_source
                FROM books
                WHERE subjects LIKE ?
                LIMIT ?
                """,
        (f"%{q}%", limit),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="book not found")
    return [dict(r) for r in rows]

@app.get("/search/description")
def search_by_description(q: str, limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
                SELECT row_id, isbn, title, author, year, publisher,
                    description, subjects, description_source, subjects_source
                FROM books
                WHERE description LIKE ?
                LIMIT ?
                """,
        (f"%{q}%", limit),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="book not found")
    return [dict(r) for r in rows]

@app.get("/search/all")
def search_everywhere(q: str, limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()

    like = f"%{q}%"
    cur.execute("""
        SELECT row_id, isbn, title, author, year, publisher,
               description, subjects
        FROM books
        WHERE title LIKE ?
           OR author LIKE ?
           OR subjects LIKE ?
           OR description LIKE ?
        LIMIT ?
    """, (like, like, like, like, limit))

    rows = cur.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="book not found")
    return [dict(r) for r in rows]
