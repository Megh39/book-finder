import sqlite3
import numpy as np
import torch,sys
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config import DB_PATH, FINAL_MASTER_DATASET_CSV

DB_FILE = DB_PATH
EMBEDDINGS_FILE = "book_embeddings.npy"
IDS_FILE = "book_row_ids.npy"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TOP_K = 5
BM25_CANDIDATES = 200

# -------------------------------
# LOAD EMBEDDINGS
# -------------------------------
book_embeddings = np.load(EMBEDDINGS_FILE)
book_row_ids = np.load(IDS_FILE)

# -------------------------------
# LOAD BOOK DATA
# -------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
    SELECT row_id, title, description, subjects, author, year
    FROM books
    WHERE description IS NOT NULL
""")
rows = cur.fetchall()
conn.close()

row_id_to_meta = {}
bm25_corpus = []
bm25_row_ids = []

for row_id, title, desc, subjects, author, year in rows:
    row_id_to_meta[row_id] = {
        "title": title,
        "author": author,
        "year": year,
        "description": desc
    }

    parts = []
    if title: parts.append(title)
    if desc: parts.append(desc)
    if subjects: parts.append(subjects)
    if author: parts.append(author)

    text = " ".join(parts).lower()
    bm25_corpus.append(text.split())
    bm25_row_ids.append(row_id)

bm25 = BM25Okapi(bm25_corpus)

# -------------------------------
# LOAD EMBEDDING MODEL
# -------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer(EMBEDDING_MODEL, device=device)

# -------------------------------
# EMBEDDING-ONLY SEARCH
# -------------------------------
def embedding_only_search(query, top_k=TOP_K):
    q_emb = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores = np.dot(book_embeddings, q_emb)
    top_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in top_idx:
        rid = int(book_row_ids[i])
        m = row_id_to_meta[rid]
        results.append({
            "row_id": rid,
            "title": m["title"],
            "author": m["author"],
            "year": m["year"],
            "score": float(scores[i])
        })

    return results

# -------------------------------
# HYBRID SEARCH (BM25 → EMBEDDING)
# -------------------------------
def hybrid_search(query, top_k=TOP_K):
    query_tokens = query.lower().split()

    bm25_scores = bm25.get_scores(query_tokens)
    top_bm25_idx = np.argsort(bm25_scores)[::-1][:BM25_CANDIDATES]
    candidate_ids = [bm25_row_ids[i] for i in top_bm25_idx]

    q_emb = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scored = []
    for rid in candidate_ids:
        emb_idx = np.where(book_row_ids == rid)[0]
        if len(emb_idx) == 0:
            continue
        sim = np.dot(book_embeddings[emb_idx[0]], q_emb)
        scored.append((rid, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    results = []
    for rid, score in top:
        m = row_id_to_meta[rid]
        results.append({
            "row_id": rid,
            "title": m["title"],
            "author": m["author"],
            "year": m["year"],
            "score": float(score)
        })

    return results

# -------------------------------
# PRETTY PRINT
# -------------------------------
def print_results(label, results):
    print(f"\n--- {label} ---")
    for i, r in enumerate(results, 1):
        print(
            f"[{i}] {r['title']} — {r['author']} ({r['year']}) "
            f"| score={r['score']:.4f}"
        )

# -------------------------------
# COMPARISON DRIVER
# -------------------------------
if __name__ == "__main__":
    test_queries = [
        "cyberpunk novel",
        "a lonely robot questioning its existence in space",
        "dark dystopian future controlled by surveillance",
        "haruki murakami loneliness",
        "introduction to linear algebra with applications"
    ]

    for q in test_queries:
        print("\n" + "=" * 90)
        print(f"QUERY: {q}")
        print("=" * 90)

        emb_results = embedding_only_search(q)
        hybrid_results = hybrid_search(q)

        print_results("Embedding-only", emb_results)
        print_results("BM25 + Embedding (Hybrid)", hybrid_results)
