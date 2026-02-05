import streamlit as st
import sys
from pathlib import Path

# Add repo root to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))
from src.search.semantic_search import (
    load_books_from_db,
    load_or_build_embeddings,
    SemanticSearchEngine,
)

st.set_page_config(
    page_title="Book Recommendation System",
    layout="centered",
)

st.title("📚 Book Recommendation System")

st.markdown(
    "Enter a natural-language description of the kind of book you want. "
    "The system will recommend relevant books using semantic similarity."
)

# -----------------------------
# Load recommender ONCE
# -----------------------------
@st.cache_resource
def load_engine():
    rows = load_books_from_db()
    embeddings, row_ids = load_or_build_embeddings(rows)
    return SemanticSearchEngine(rows, embeddings, row_ids)

engine = load_engine()

# -----------------------------
# UI
# -----------------------------
query = st.text_input(
    "Describe the book you want",
    placeholder="e.g. a lonely robot questioning its existence in space",
)

mode = st.selectbox(
    "Recommendation mode",
    ["Semantic", "Hybrid"],
)

TOP_K = 5

if st.button("Recommend"):
    if not query.strip():
        st.warning("Please enter a description.")
    else:
        with st.spinner("Generating recommendations..."):
            if mode == "Semantic":
                results = engine.embedding_only_search(query, top_k=TOP_K)
            else:
                results = engine.hybrid_search(query, top_k=TOP_K)

        if not results:
            st.info("No recommendations found.")
        else:
            st.subheader("Recommended Books")
            for i, r in enumerate(results, 1):
                st.markdown(
                    f"**{i}. {r['title']}**  \n"
                    f"*{r['author']} ({r['year']})*"
                )
