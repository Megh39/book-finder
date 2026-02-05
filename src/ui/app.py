import streamlit as st
import requests

# CHANGE this to your deployed FastAPI backend URL
API_BASE = "https://YOUR-BACKEND-URL.onrender.com"

st.set_page_config(page_title="Book Recommendation System")

st.title("📚 Book Recommendation System")

st.markdown(
    "Describe the kind of book you want. "
    "The system will recommend relevant books."
)

query = st.text_input(
    "Enter description",
    placeholder="e.g. a lonely robot questioning its existence in space"
)

mode = st.selectbox(
    "Recommendation mode",
    ["semantic", "hybrid", "title"]
)

TOP_K = 5

if st.button("Recommend"):
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Finding recommendations..."):
            if mode == "title":
                url = f"{API_BASE}/search/title?q={query}&limit={TOP_K}"
            elif mode == "semantic":
                url = f"{API_BASE}/search/semantic?q={query}&top_k={TOP_K}"
            else:
                url = f"{API_BASE}/search/hybrid?q={query}&top_k={TOP_K}"

            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                results = resp.json()
            except Exception as e:
                st.error(f"Backend error: {e}")
                st.stop()

        if not results:
            st.info("No recommendations found.")
        else:
            st.subheader("Recommended Books")
            for i, b in enumerate(results, 1):
                st.markdown(
                    f"**{i}. {b['title']}**  \n"
                    f"*{b['author']} ({b['year']})*"
                )
