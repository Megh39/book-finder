import pandas as pd
import re
import html

INPUT = "../data/processed/FINAL_MASTER_DATASET.csv"
OUTPUT = "../data/processed/FINAL_MASTER_WITH_FINAL_TEXT.csv"

BAD_TEXT = {
    "nan",
    "none",
    "null",
    "n/a",
    "na",
    "description not available",
    "not available",
    "no description",
    "no description available",
}


def strip_html(s: str) -> str:
    s = html.unescape(s)
    s = re.sub(r"(?i)<br\s*/?>", " ", s)  # <br> -> space
    s = re.sub(r"<[^>]+>", " ", s)  # remove tags
    s = " ".join(s.split())  # normalize whitespace
    return s.strip()


def remove_toc_noise(s: str) -> str:
    if not s:
        return s
    low = s.lower()
    for key in ["table of contents", "contents:"]:
        idx = low.find(key)
        if idx != -1:
            return s[:idx].strip()
    return s


def clean_text(x):
    if pd.isna(x):
        return None

    s = str(x).strip()
    if not s:
        return None

    # common encoding garbage fixes
    s = (
        s.replace("â€™", "'")
        .replace("â€œ", '"')
        .replace("â€", '"')
        .replace("â€”", "-")
        .replace("â€“", "-")
    )

    s = strip_html(s)
    s = remove_toc_noise(s)

    if not s:
        return None

    if s.lower() in BAD_TEXT:
        return None

    return s


# column -> source label (what you want in CSV)
DESC_SOURCES = {
    "summary": "koha_opac",
    "ol_description": "openlibrary",
    "oa_abstract": "openalex",
}

SUBJ_SOURCES = {
    "subjects": "koha_opac",
    "ol_subjects": "openlibrary",
    "oa_concept_tags": "openalex",
}


def pick_first_with_source(row, cols, source_map):
    for c in cols:
        val = clean_text(row.get(c))
        if val is not None:
            return val, source_map.get(c, "unknown")
    return None, None


def main():
    df = pd.read_csv(INPUT, engine="python", on_bad_lines="skip")
    df = df.reset_index(drop=True)
    df["row_id"] = df.index

    desc_cols = ["summary", "ol_description", "oa_abstract"]
    df["final_description"], df["final_description_source"] = zip(
        *df.apply(lambda r: pick_first_with_source(r, desc_cols, DESC_SOURCES), axis=1)
    )

    # SUBJECTS priority: Koha(OPAC) -> OpenLibrary -> OpenAlex
    sub_cols = ["subjects", "ol_subjects", "oa_concept_tags"]
    df["final_subjects"], df["final_subjects_source"] = zip(
        *df.apply(lambda r: pick_first_with_source(r, sub_cols, SUBJ_SOURCES), axis=1)
    )

    df["has_final_description"] = df["final_description"].notna().astype(int)
    df["has_final_subjects"] = df["final_subjects"].notna().astype(int)

    print("Rows:", len(df))
    print("Final descriptions:", df["has_final_description"].sum())
    print("Final subjects:", df["has_final_subjects"].sum())

    print("\nDescription source counts:")
    print(df["final_description_source"].value_counts(dropna=False))

    print("\nSubjects source counts:")
    print(df["final_subjects_source"].value_counts(dropna=False))

    df.to_csv(OUTPUT, index=False)
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
