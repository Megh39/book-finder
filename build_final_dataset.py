import os
import pandas as pd


# ----------------- Paths -----------------
BASE_CSV = "./data/updated_books_data.csv"

KOHA_CSV = "./data/interim/koha_enriched.csv"
OPENLIB_CSV = "./data/interim/openlibrary_enriched.csv"
OPENALEX_CSV = "./data/interim/openalex_enriched.csv"

OUT_DIR = "./data/processed"
OUT_FILE = os.path.join(OUT_DIR, "FINAL_MASTER_DATASET.csv")


# ----------------- Helpers -----------------
def safe_read_csv(path, sep=","):
    return pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")


def clean_isbn_col(df, col="ISBN"):
    if col not in df.columns:
        return df
    df[col] = df[col].astype(str).str.strip()
    df.loc[df[col].isin(["nan", "None", "NaN", ""]), col] = None
    return df


def dedupe_openlibrary_best(ol: pd.DataFrame) -> pd.DataFrame:
    if "ISBN" not in ol.columns:
        return ol

    ol = ol.copy()
    ol = clean_isbn_col(ol, "ISBN")

    if "status" not in ol.columns:
        return ol.drop_duplicates(subset=["ISBN"], keep="first")

    def has_text(col):
        return ol[col].notna() & (ol[col].astype(str).str.strip() != "") if col in ol.columns else False

    ol["is_ok"] = (ol["status"].astype(str).str.strip().str.lower() == "ok")
    ol["has_desc"] = has_text("description")
    ol["has_subj"] = has_text("subjects")
    ol["has_title"] = has_text("title")

    ol = ol.sort_values(
        by=["ISBN", "is_ok", "has_desc", "has_subj", "has_title"],
        ascending=[True, False, False, False, False]
    )

    ol_best = ol.drop_duplicates(subset=["ISBN"], keep="first").copy()
    ol_best = ol_best.drop(columns=["is_ok", "has_desc", "has_subj", "has_title"])

    return ol_best


def norm_title(x):
    if pd.isna(x):
        return ""
    s = str(x).lower().strip()
    for ch in [":", ";", ",", ".", "(", ")", "[", "]", "{", "}", "'", '"', "/", "\\", "|"]:
        s = s.replace(ch, " ")
    s = " ".join(s.split())
    return s


# ----------------- Main -----------------
def main():
    # ---- Check files ----
    for f in [BASE_CSV, KOHA_CSV, OPENLIB_CSV, OPENALEX_CSV]:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Missing required file: {f}")

    os.makedirs(OUT_DIR, exist_ok=True)

    # ---- Load base ----
    base = safe_read_csv(BASE_CSV)
    if "ISBN" not in base.columns:
        raise ValueError("Base file must contain column: ISBN")
    if "Title" not in base.columns:
        raise ValueError("Base file must contain column: Title")

    base = clean_isbn_col(base, "ISBN")

    # ---- Merge Koha (by ISBN) ----
    koha = safe_read_csv(KOHA_CSV, sep=";")  # Koha uses semicolon
    koha = clean_isbn_col(koha, "ISBN")
    koha = koha.drop_duplicates(subset=["ISBN"], keep="first")

    m1 = base.merge(koha, on="ISBN", how="left")
    print("Koha matched:", m1["status"].notna().sum() if "status" in m1.columns else 0, "/", len(m1))

    # ---- Merge OpenLibrary (by ISBN) ----
    ol = safe_read_csv(OPENLIB_CSV)
    ol = clean_isbn_col(ol, "ISBN")

    if "ol_status" in ol.columns:
        ol_best = ol.drop_duplicates(subset=["ISBN"], keep="first")
    else:
        ol_best = dedupe_openlibrary_best(ol)
        ol_best = ol_best.rename(columns={c: f"ol_{c}" for c in ol_best.columns if c != "ISBN"})

    m2 = m1.merge(ol_best, on="ISBN", how="left")

    if "ol_status" in m2.columns:
        print("OpenLibrary matched:", m2["ol_status"].notna().sum(), "/", len(m2))
    else:
        print("OpenLibrary matched: 0 /", len(m2), "(no ol_status column found)")

    # ---- Merge OpenAlex (by Title key) ----
    oa = safe_read_csv(OPENALEX_CSV)

    # detect OA title column
    if "Title" in oa.columns:
        oa_title_col = "Title"
    elif "oa_Title" in oa.columns:
        oa_title_col = "oa_Title"
    else:
        raise ValueError("OpenAlex file must contain 'Title' or 'oa_Title' column")

    # build title_key
    m2["title_key"] = m2["Title"].map(norm_title)
    oa["title_key"] = oa[oa_title_col].map(norm_title)

    # choose similarity column if present
    sim_col = None
    if "similarity" in oa.columns:
        sim_col = "similarity"
    elif "oa_similarity" in oa.columns:
        sim_col = "oa_similarity"

    # keep best OpenAlex row per title_key
    if sim_col:
        oa = oa.sort_values(["title_key", sim_col], ascending=[True, False])
    oa_best = oa.drop_duplicates("title_key", keep="first").copy()


    final = m2.merge(oa_best, on="title_key", how="left")

    if "oa_status" in final.columns:
        print("OpenAlex matched:", final["oa_status"].notna().sum(), "/", len(final))
    else:
        print("OpenAlex matched: 0 /", len(final), "(no oa_status column found)")

    # cleanup helper
    final = final.drop(columns=["title_key"], errors="ignore")

    # ---- Save ----
    final.to_csv(OUT_FILE, index=False)
    print("Saved:", OUT_FILE)

    # ---- Quick summary ----
    if "status" in final.columns:
        print("Koha OK:", (final["status"].astype(str).str.strip() == "ok").sum())
    if "ol_status" in final.columns:
        print("OpenLibrary OK:", (final["ol_status"].astype(str).str.strip() == "ok").sum())
    if "oa_status" in final.columns:
        print("OpenAlex OK exact:", (final["oa_status"] == "ok_exact_title").sum())
        print("OpenAlex OK high:", (final["oa_status"] == "ok_high_confidence").sum())


if __name__ == "__main__":
    main()
