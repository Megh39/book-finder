import pandas as pd
from config import ORIGINAL_DATA_CSV,UPDATED_BOOKS_CSV
INPUT_CSV = ORIGINAL_DATA_CSV
OUTPUT_CSV = UPDATED_BOOKS_CSV

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
