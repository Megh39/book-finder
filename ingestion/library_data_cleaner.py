import pandas as pd

INPUT_CSV = "../data/raw/books data.csv"
OUTPUT_CSV = "../data/updated_books_data.csv"

df = pd.read_csv(INPUT_CSV, engine="python", on_bad_lines="skip",encoding="cp1252")
before = len(df)
df = df.drop_duplicates(
    subset=["Title", "Page(s)", "Year", "Author/Editor", "ISBN"],
    keep="first"
)

df.to_csv(OUTPUT_CSV, index=False)

print(f"Saved deduped file -> {OUTPUT_CSV}")
print(f"Rows before: {before}")
print(f"Rows after : {len(df)}")
