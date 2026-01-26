import os
import time
import requests
import pandas as pd

BASE = "https://openlibrary.org"

# ---- Input/Output ----
INPUT_CSV = "../data/updated_books_data.csv"          # your cleaned deduped library file
OUTPUT_CSV = "../data/interim/openlibrary_enriched.csv"

# ---- Tunables ----
SAVE_EVERY = 20
SLEEP = 0.3

MAX_RETRIES = 5
TIMEOUT = 20

session = requests.Session()
session.headers.update({
    "User-Agent": "Megh-OpenLibrary-Enricher/1.0"
})


# ----------------- Helpers -----------------
def clean_isbn(isbn):
    if pd.isna(isbn):
        return None
    s = str(isbn).strip().replace("-", "").replace(" ", "")
    return s if s and s.lower() != "nan" else None


def fetch_json(url):
    """
    Returns: (json_or_none, status_code_or_error)
    status_code_or_error can be 200, 404, or "error"
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(url, timeout=TIMEOUT)

            if r.status_code == 200:
                return r.json(), 200

            if r.status_code == 404:
                return None, 404

            # Other status codes: retry
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
        ):
            pass

        wait = min(2 ** attempt, 20)
        print(f"[retry {attempt}/{MAX_RETRIES}] waiting {wait}s -> {url}")
        time.sleep(wait)

    return None, "error"


def parse_description(desc):
    if desc is None:
        return None
    if isinstance(desc, str):
        d = desc.strip()
        return d if d else None
    if isinstance(desc, dict) and "value" in desc:
        d = str(desc["value"]).strip()
        return d if d else None
    return None


def get_author_name(author_key):
    data, code = fetch_json(f"{BASE}{author_key}.json")
    if not data or code != 200:
        return None
    return data.get("name")


# ----------------- Enrichment -----------------
def enrich_one(row_id, isbn):
    isbn = clean_isbn(isbn)
    if not isbn:
        return {"row_id": row_id, "ISBN": None, "ol_status": "invalid_isbn"}

    edition, code = fetch_json(f"{BASE}/isbn/{isbn}.json")
    if code == 404 or edition is None:
        return {"row_id": row_id, "ISBN": isbn, "ol_status": "edition_not_found"}
    if code != 200:
        return {"row_id": row_id, "ISBN": isbn, "ol_status": "error_fetch_edition"}

    title = edition.get("title")
    publish_date = edition.get("publish_date")
    number_of_pages = edition.get("number_of_pages")

    publishers = edition.get("publishers", [])
    publisher = publishers[0] if isinstance(publishers, list) and publishers else None

    author_names = []
    for a in edition.get("authors", []):
        if isinstance(a, dict) and a.get("key"):
            name = get_author_name(a["key"])
            if name:
                author_names.append(name)
    authors = "; ".join(author_names) if author_names else None

    description = parse_description(edition.get("description"))

    work_key = None
    works = edition.get("works", [])
    if isinstance(works, list) and works:
        w0 = works[0]
        if isinstance(w0, dict):
            work_key = w0.get("key")

    subjects = None
    if work_key:
        work, wcode = fetch_json(f"{BASE}{work_key}.json")
        if work and wcode == 200:
            work_desc = parse_description(work.get("description"))
            if work_desc:
                description = work_desc

            subs = work.get("subjects")
            if isinstance(subs, list) and subs:
                subjects = "; ".join([str(s) for s in subs if s])

    return {
        "row_id": row_id,
        "ISBN": isbn,
        "ol_status": "ok",
        "ol_title": title,
        "ol_authors": authors,
        "ol_publisher": publisher,
        "ol_publish_date": publish_date,
        "ol_number_of_pages": number_of_pages,
        "ol_work_key": work_key,
        "ol_description": description,
        "ol_subjects": subjects,
    }


# ----------------- Resume + Saving -----------------
def load_done_ids():
    if not os.path.exists(OUTPUT_CSV):
        return set()

    try:
        old = pd.read_csv(OUTPUT_CSV, engine="python", on_bad_lines="skip")
        if "row_id" not in old.columns:
            return set()

        return set(pd.to_numeric(old["row_id"], errors="coerce").dropna().astype(int))
    except Exception:
        return set()


def save_append(rows):
    if not rows:
        return

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    df_new = pd.DataFrame(rows)
    file_exists = os.path.exists(OUTPUT_CSV)
    df_new.to_csv(OUTPUT_CSV, mode="a", index=False, header=not file_exists)


# ----------------- Main -----------------
def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, engine="python", on_bad_lines="skip")

    if "row_id" not in df.columns:
        df = df.reset_index(drop=True)
        df["row_id"] = df.index

    if "ISBN" not in df.columns:
        raise ValueError("Input CSV must contain column 'ISBN'")

    done = load_done_ids()
    print("Already done:", len(done))

    buffer = []
    total = len(df)

    for i in range(total):
        row_id = int(df.loc[i, "row_id"])
        if row_id in done:
            continue

        isbn = df.loc[i, "ISBN"]
        print(f"[{i+1}/{total}] row_id={row_id} isbn={isbn}")

        try:
            out = enrich_one(row_id, isbn)
        except Exception as e:
            out = {
                "row_id": row_id,
                "ISBN": clean_isbn(isbn),
                "ol_status": f"error:{type(e).__name__}",
            }

        buffer.append(out)

        if len(buffer) >= SAVE_EVERY:
            save_append(buffer)
            print("Saved:", len(buffer))
            buffer = []

        time.sleep(SLEEP)

    save_append(buffer)
    print("Done ->", OUTPUT_CSV)


if __name__ == "__main__":
    main()
