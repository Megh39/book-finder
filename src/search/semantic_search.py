import sqlite3
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import torch

from src.config import DB_PATH

# -------------------------------
# CONFIG
# -------------------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDINGS_FILE = Path("book_embeddings.npy")
ROW_IDS_FILE = Path("book_row_ids.npy")

TOP_K = 5
BM25_CANDIDATES = 200

# -------------------------------
# DB LOAD
# -------------------------------
def load_books_from_db():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("""
        SELECT row_id, title, author, year, description, subjects
        FROM books
        WHERE description IS NOT NULL
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        raise RuntimeError("No rows with descriptions found in DB")

    return rows


# -------------------------------
# EMBEDDING GENERATION
# -------------------------------
def build_search_text(row):
    _, title, author, _, description, subjects = row

    parts = []
    if title: parts.append(title)
    if description: parts.append(description)
    if subjects: parts.append(subjects)
    if author: parts.append(author)

    return " ".join(parts)


def generate_embeddings(rows):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)

    texts = [build_search_text(r) for r in rows]
    row_ids = np.array([r[0] for r in rows], dtype=np.int64)

    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    assert len(embeddings) == len(row_ids), "Embedding/ID alignment broken"

    np.save(EMBEDDINGS_FILE, embeddings)
    np.save(ROW_IDS_FILE, row_ids)

    return embeddings, row_ids


# -------------------------------
# LOAD OR BUILD EMBEDDINGS
# -------------------------------
def load_or_build_embeddings(rows):
    if EMBEDDINGS_FILE.exists() and ROW_IDS_FILE.exists():
        embeddings = np.load(EMBEDDINGS_FILE)
        row_ids = np.load(ROW_IDS_FILE)

        if len(embeddings) != len(row_ids):
            raise RuntimeError("Saved embeddings and row_ids length mismatch")

        return embeddings, row_ids

    print("[INFO] Embeddings not found. Regenerating from DB...")
    return generate_embeddings(rows)


# -------------------------------
# BM25 INDEX
# -------------------------------
def build_bm25_index(rows):
    corpus = []
    row_ids = []

    for r in rows:
        text = build_search_text(r).lower()
        corpus.append(text.split())
        row_ids.append(r[0])

    return BM25Okapi(corpus), row_ids


# -------------------------------
# SEARCH ENGINE
# -------------------------------
class SemanticSearchEngine:
    def __init__(self, rows, embeddings, emb_row_ids):
        self.rows = rows
        self.embeddings = embeddings
        self.emb_row_ids = emb_row_ids

        self.row_id_to_meta = {
            r[0]: {
                "title": r[1],
                "author": r[2],
                "year": r[3],
            }
            for r in rows
        }

        self.row_id_to_emb_idx = {
            rid: i for i, rid in enumerate(emb_row_ids)
        }

        self.bm25, self.bm25_row_ids = build_bm25_index(rows)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)

    def embedding_only_search(self, query, top_k=TOP_K):
        q_emb = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        scores = np.dot(self.embeddings, q_emb)
        top_idx = np.argsort(scores)[::-1][:top_k]

        return self._format_results(top_idx, scores)

    def hybrid_search(self, query, top_k=TOP_K):
        tokens = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokens)

        top_bm25_idx = np.argsort(bm25_scores)[::-1][:BM25_CANDIDATES]
        candidate_ids = [self.bm25_row_ids[i] for i in top_bm25_idx]

        q_emb = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        scored = []
        for rid in candidate_ids:
            emb_idx = self.row_id_to_emb_idx.get(rid)
            if emb_idx is None:
                continue
            sim = float(np.dot(self.embeddings[emb_idx], q_emb))
            scored.append((emb_idx, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

        return self._format_results(
            [i for i, _ in top],
            np.array([s for _, s in top]),
            direct_scores=True,
        )

    def _format_results(self, indices, scores, direct_scores=False):
        results = []

        for rank, idx in enumerate(indices):
            rid = int(self.emb_row_ids[idx])
            meta = self.row_id_to_meta[rid]

            score = scores[rank] if direct_scores else scores[idx]

            results.append({
                "row_id": rid,
                "title": meta["title"],
                "author": meta["author"],
                "year": meta["year"],
                "score": float(score),
            })

        return results


# -------------------------------
# DEMO DRIVER
# -------------------------------
def print_results(label, results):
    print(f"\n--- {label} ---")
    for i, r in enumerate(results, 1):
        print(
            f"[{i}] {r['title']} — {r['author']} ({r['year']}) "
            f"| score={r['score']:.4f}"
        )


if __name__ == "__main__":
    rows = load_books_from_db()
    embeddings, emb_row_ids = load_or_build_embeddings(rows)

    engine = SemanticSearchEngine(rows, embeddings, emb_row_ids)

    test_queries = [
        "cyberpunk novel",
        "a lonely robot questioning its existence in space",
        "dark dystopian future controlled by surveillance",
        "haruki murakami loneliness",
        "introduction to linear algebra with applications",
    ]

    for q in test_queries:
        print("\n" + "=" * 90)
        print(f"QUERY: {q}")
        print("=" * 90)

        print_results(
            "Embedding-only",
            engine.embedding_only_search(q),
        )

        print_results(
            "BM25 + Embedding (Hybrid)",
            engine.hybrid_search(q),
        )
