import sqlite3
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config import DB_PATH, FINAL_MASTER_WITH_FINAL_TEXT_CSV

DB_FILE = DB_PATH              # same DB you populated
EMBEDDINGS_FILE = "book_embeddings.npy"
IDS_FILE = "book_row_ids.npy"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5

# -------------------------------
# LOAD EMBEDDINGS
# -------------------------------
book_embeddings = np.load(EMBEDDINGS_FILE)
book_row_ids = np.load(IDS_FILE)

# embeddings were saved normalized; keep them normalized
# shape: (N, 384)

print("Loaded embeddings:", book_embeddings.shape)

# -------------------------------
# LOAD METADATA
# -------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Build a lookup: row_id -> metadata
placeholders = ",".join(["?"] * len(book_row_ids))
cur.execute(
    f"""
    SELECT row_id, title, author, year
    FROM books
    WHERE row_id IN ({placeholders})
    """,
    tuple(book_row_ids.tolist()),
)

rows = cur.fetchall()
conn.close()

meta = {r[0]: {"title": r[1], "author": r[2], "year": r[3]} for r in rows}

# -------------------------------
# LOAD MODEL (GPU IF AVAILABLE)
# -------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer(EMBEDDING_MODEL, device=device)

# -------------------------------
# SEARCH FUNCTION
# -------------------------------
def pretty_print_results(query, results, db_path=DB_FILE, snippet_len=300):
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for i, r in enumerate(results, start=1):
        cur.execute(
            "SELECT description FROM books WHERE row_id = ?",
            (r["row_id"],)
        )
        row = cur.fetchone()
        desc = row[0] if row and row[0] else ""
        snippet = desc[:snippet_len].replace("\n", " ")

        print(f"\n[{i}] {r['title']}")
        print(f"    Author : {r['author']}")
        print(f"    Year   : {r['year']}")
        print(f"    Score  : {r['score']:.4f}")
        print(f"    Snip   : {snippet}...")

    conn.close()
    print("\n")

def search(query, top_k=TOP_K):
    # Embed query (normalize to match stored embeddings)
    q_emb = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # Cosine similarity = dot product (since normalized)
    scores = np.dot(book_embeddings, q_emb)

    top_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in top_idx:
        row_id = int(book_row_ids[i])
        m = meta.get(row_id, {})
        results.append({
            "row_id": row_id,
            "title": m.get("title"),
            "author": m.get("author"),
            "year": m.get("year"),
            "score": float(scores[i]),
        })

    return results

# -------------------------------
# CLI
# -------------------------------
# if __name__ == "__main__":
#     while True:
#         q = input("\nQuery (or 'exit'): ").strip()
#         if q.lower() in {"exit", "quit"}:
#             break

#         res = search(q)
#         print("\nTop results:\n")
#         for r in res:
#             print(f"{r['title']} — {r['author']} ({r['year']}) | score={r['score']:.4f}")
if __name__ == "__main__":
    test_queries = [
        "a lonely robot questioning its existence in space",
        "dark dystopian future controlled by surveillance",
        "introduction to linear algebra with applications",
        "cyberpunk novel",
        "philosophical book about artificial intelligence",
        "haruki murakami loneliness"
    ]

    for q in test_queries:
        results = search(q, top_k=5)
        pretty_print_results(q, results)
