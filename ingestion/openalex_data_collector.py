import os
import time
import requests
import pandas as pd
from difflib import SequenceMatcher
from config import UPDATED_BOOKS_CSV,OPENALEX_ENRICHED_CSV
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

BASE = "https://api.openalex.org"
HEADERS = {"User-Agent": "Megh-OpenAlex-Enricher/1.0"}

# ---- Input/Output ----
INPUT_CSV = UPDATED_BOOKS_CSV              # must contain Title
OUTPUT_CSV = OPENALEX_ENRICHED_CSV

# ---- Tunables ----
SAVE_EVERY = 5
PER_PAGE = 5
SLEEP = 0.4
SIM_THRESHOLD = 0.92


# ----------------- Helpers -----------------
def norm_title(t):
    if pd.isna(t):
        return None
    t = str(t).strip().lower()
    if not t:
        return None

    for ch in [":", ";", ",", ".", "(", ")", "[", "]", "{", "}", "'", '"', "/", "\\", "|"]:
        t = t.replace(ch, " ")

    t = " ".join(t.split())
    return t if t else None


def title_similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def reconstruct_abstract(abstract_inverted_index):
    """
    OpenAlex abstract format:
    { "word": [pos1, pos2], ... }
    Rebuild into ordered text.
    """
    if not isinstance(abstract_inverted_index, dict):
        return None

    positions = {}
    for word, pos_list in abstract_inverted_index.items():
        if not isinstance(pos_list, list):
            continue
        for p in pos_list:
            positions[p] = word

    if not positions:
        return None

    max_pos = max(positions.keys())
    words = [positions.get(i, "") for i in range(max_pos + 1)]
    text = " ".join([w for w in words if w]).strip()
    return text if text else None


def get_json(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def search_openalex_by_title(title):
    data = get_json(f"{BASE}/works", params={"search": title, "per-page": PER_PAGE})
    return data.get("results", [])


def extract_concepts(work, top_k=10):
    concepts = work.get("concepts", [])
    if not isinstance(concepts, list) or not concepts:
        return None

    concepts_sorted = sorted(concepts, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
    names = [c.get("display_name") for c in concepts_sorted if c.get("display_name")]
    return "; ".join(names) if names else None


# ----------------- Resume + Saving -----------------
def load_done_ids(out_file):
    if not os.path.exists(out_file):
        return set()
    try:
        old = pd.read_csv(out_file, engine="python", on_bad_lines="skip")
        if "row_id" not in old.columns:
            return set()
        return set(pd.to_numeric(old["row_id"], errors="coerce").dropna().astype(int))
    except Exception:
        return set()


def save_append(rows, out_file):
    if not rows:
        return
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    df_new = pd.DataFrame(rows)
    file_exists = os.path.exists(out_file)
    df_new.to_csv(out_file, mode="a", index=False, header=not file_exists)


# ----------------- Main -----------------
def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, engine="python", on_bad_lines="skip")

    if "Title" not in df.columns:
        raise ValueError("Input must contain column: Title")

    if "row_id" not in df.columns:
        df = df.reset_index(drop=True)
        df["row_id"] = df.index

    done = load_done_ids(OUTPUT_CSV)
    print("Already done rows:", len(done))

    buffer = []
    total = len(df)

    for i in range(total):
        row_id = int(df.loc[i, "row_id"])
        if row_id in done:
            continue

        raw_title = df.loc[i, "Title"]
        title_norm = norm_title(raw_title)

        print(f"[{i+1}/{total}] row_id={row_id} | {raw_title}")

        if not title_norm:
            buffer.append({
                "row_id": row_id,
                "oa_Title": raw_title,
                "oa_openalex_id": None,
                "oa_openalex_title": None,
                "oa_doi": None,
                "oa_type": None,
                "oa_year": None,
                "oa_cited_by_count": None,
                "oa_similarity": None,
                "oa_concept_tags": None,
                "oa_abstract": None,
                "oa_status": "empty_title"
            })
            continue

        try:
            candidates = search_openalex_by_title(raw_title)

            if not candidates:
                buffer.append({
                    "row_id": row_id,
                    "oa_Title": raw_title,
                    "oa_openalex_id": None,
                    "oa_openalex_title": None,
                    "oa_doi": None,
                    "oa_type": None,
                    "oa_year": None,
                    "oa_cited_by_count": None,
                    "oa_similarity": None,
                    "oa_concept_tags": None,
                    "oa_abstract": None,
                    "oa_status": "no_candidates"
                })
                continue

            best = None
            best_sim = -1

            for w in candidates:
                oa_title = w.get("display_name")
                if not oa_title:
                    continue

                sim = title_similarity(title_norm, norm_title(oa_title))

                if sim > best_sim:
                    best_sim = sim
                    best = w

                if norm_title(oa_title) == title_norm:
                    best_sim = 1.0
                    best = w
                    break

            if not best:
                buffer.append({
                    "row_id": row_id,
                    "oa_Title": raw_title,
                    "oa_openalex_id": None,
                    "oa_openalex_title": None,
                    "oa_doi": None,
                    "oa_type": None,
                    "oa_year": None,
                    "oa_cited_by_count": None,
                    "oa_similarity": None,
                    "oa_concept_tags": None,
                    "oa_abstract": None,
                    "oa_status": "no_valid_candidate"
                })
                continue

            if best_sim == 1.0:
                accepted = True
                status = "ok_exact_title"
            elif best_sim >= SIM_THRESHOLD:
                accepted = True
                status = "ok_high_confidence"
            else:
                accepted = False
                status = "rejected_low_confidence"

            buffer.append({
                "row_id": row_id,
                "oa_Title": raw_title,
                "oa_openalex_id": best.get("id") if accepted else None,
                "oa_openalex_title": best.get("display_name"),
                "oa_doi": best.get("doi") if accepted else None,
                "oa_type": best.get("type"),
                "oa_year": best.get("publication_year"),
                "oa_cited_by_count": best.get("cited_by_count"),
                "oa_similarity": round(best_sim, 4),
                "oa_concept_tags": extract_concepts(best) if accepted else None,
                "oa_abstract": reconstruct_abstract(best.get("abstract_inverted_index")) if accepted else None,
                "oa_status": status
            })

        except Exception as e:
            buffer.append({
                "row_id": row_id,
                "oa_Title": raw_title,
                "oa_openalex_id": None,
                "oa_openalex_title": None,
                "oa_doi": None,
                "oa_type": None,
                "oa_year": None,
                "oa_cited_by_count": None,
                "oa_similarity": None,
                "oa_concept_tags": None,
                "oa_abstract": None,
                "oa_status": f"error:{type(e).__name__}"
            })

        if len(buffer) >= SAVE_EVERY:
            save_append(buffer, OUTPUT_CSV)
            print("Saved:", len(buffer))
            buffer = []

        time.sleep(SLEEP)

    if buffer:
        save_append(buffer, OUTPUT_CSV)
        print("Final save:", len(buffer))

    print("Done ->", OUTPUT_CSV)


if __name__ == "__main__":
    main()
