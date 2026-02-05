import sqlite3
from src.config import DB_PATH


def connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    return sqlite3.connect(str(DB_PATH))


def scalar(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchone()[0]


def main():
    conn = connect()
    cur = conn.cursor()

    print("\n=== DATABASE OVERVIEW ===")
    total_rows = scalar(conn, "SELECT COUNT(*) FROM books")
    print(f"Total rows: {total_rows}")

    print("\n=== ISBN STATISTICS ===")
    print("Distinct ISBNs:",
          scalar(conn, "SELECT COUNT(DISTINCT isbn) FROM books WHERE isbn IS NOT NULL"))
    print("Missing ISBNs:",
          scalar(conn, "SELECT COUNT(*) FROM books WHERE isbn IS NULL"))

    print("\n=== MISSING VALUES ===")
    print("Missing descriptions:",
          scalar(conn, "SELECT COUNT(*) FROM books WHERE description IS NULL"))
    print("Missing subjects:",
          scalar(conn, "SELECT COUNT(*) FROM books WHERE subjects IS NULL"))
    print("Missing years:",
          scalar(conn, "SELECT COUNT(*) FROM books WHERE year IS NULL"))

    print("\n=== DESCRIPTION SOURCE DISTRIBUTION ===")
    cur.execute("""
        SELECT description_source, COUNT(*)
        FROM books
        GROUP BY description_source
        ORDER BY COUNT(*) DESC
    """)
    for src, cnt in cur.fetchall():
        print(f"{src}: {cnt}")

    print("\n=== SUBJECT SOURCE DISTRIBUTION ===")
    cur.execute("""
        SELECT subjects_source, COUNT(*)
        FROM books
        GROUP BY subjects_source
        ORDER BY COUNT(*) DESC
    """)
    for src, cnt in cur.fetchall():
        print(f"{src}: {cnt}")

    print("\n=== YEAR STATISTICS ===")
    cur.execute("""
        SELECT MIN(year), MAX(year), AVG(year)
        FROM books
        WHERE year IS NOT NULL
    """)
    min_y, max_y, avg_y = cur.fetchone()
    print(f"Min year: {min_y}")
    print(f"Max year: {max_y}")
    print(f"Avg year: {avg_y:.2f}" if avg_y else "Avg year: NA")

    print("\n=== DESCRIPTION LENGTH ===")
    cur.execute("""
        SELECT AVG(LENGTH(description)), MAX(LENGTH(description))
        FROM books
        WHERE description IS NOT NULL
    """)
    avg_len, max_len = cur.fetchone()
    print(f"Average length: {avg_len:.2f}")
    print(f"Max length: {max_len}")

    print("\n=== TOP 10 SUBJECTS ===")

    cur.execute("SELECT subjects FROM books WHERE subjects IS NOT NULL")
    rows = cur.fetchall()

    subject_counts = {}

    for (subjects,) in rows:
        for s in subjects.split(";"):
            s = s.strip()
            if not s:
                continue
            subject_counts[s] = subject_counts.get(s, 0) + 1

    top_subjects = sorted(
        subject_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    for subject, cnt in top_subjects:
        print(f"{subject}: {cnt}")


    conn.close()
    print("\n=== DONE ===\n")


if __name__ == "__main__":
    main()
