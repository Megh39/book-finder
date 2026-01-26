import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import UPDATED_BOOKS_CSV,KOHA_ENRICHED_CSV

BASE = "https://opac.daiict.ac.in"

SAVE_EVERY = 5
SLEEP_BETWEEN = 0.5

MAX_BLOCK_RETRIES = 3
SEARCH_TIMEOUT = 30000
CLICK_TIMEOUT = 15000
DETAIL_WAIT_TIMEOUT = 5000


def clean_isbn(x):
    if pd.isna(x):
        return None
    s = str(x).strip().replace("-", "").replace(" ", "")
    if not s:
        return None
    s = s.upper()
    if s.isdigit() and len(s) < 10:
        s = s.zfill(10)
    return s


def is_block_page(html_lower: str) -> bool:
    keywords = [
        "captcha", "cloudflare", "security check", "verify you are human",
        "access denied", "attention required", "checking your browser",
        "unusual traffic", "blocked", "request blocked", "forbidden",
    ]
    return any(k in html_lower for k in keywords)


def extract_subjects_and_summary(html: str):
    soup = BeautifulSoup(html, "html.parser")

    subjects = []
    subjects_block = soup.select_one("span.results_summary.subjects ul.resource_list")
    if subjects_block:
        for a in subjects_block.select("a.subject"):
            txt = a.get_text(strip=True)
            if txt:
                subjects.append(txt)

    summary = None
    summary_span = soup.select_one("span.results_summary.summary")
    if summary_span:
        label = summary_span.select_one("span.label")
        if label:
            label.extract()
        summary = summary_span.get_text(" ", strip=True)

    return ("; ".join(subjects) if subjects else None), summary


def safe_read_csv(path, sep=","):
    return pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")


def row_score(row: dict) -> int:
    if not row:
        return -999

    status = str(row.get("status", "")).strip().lower()
    subjects = row.get("subjects")
    summary = row.get("summary")

    has_subjects = isinstance(subjects, str) and subjects.strip() != ""
    has_summary = isinstance(summary, str) and summary.strip() != ""

    base = {
        "ok": 50,
        "found_but_empty": 30,
        "timeout": 10,
        "security_check_failed": 5,
        "no_results": 0,
    }.get(status, 8)

    bonus = 0
    if has_subjects:
        bonus += 20
    if has_summary:
        bonus += 20

    return base + bonus


def pick_better_row(old_row: dict, new_row: dict) -> dict:
    if not old_row:
        return new_row
    if not new_row:
        return old_row
    return new_row if row_score(new_row) > row_score(old_row) else old_row


def load_existing_best(output_csv):
    """
    Load existing output and keep best row per ISBN.
    """
    if not os.path.exists(output_csv):
        return {}

    df = safe_read_csv(output_csv, sep=";")
    if "ISBN" not in df.columns:
        return {}

    df["ISBN_norm"] = df["ISBN"].map(clean_isbn)
    df = df.dropna(subset=["ISBN_norm"])

    best = {}
    for _, r in df.iterrows():
        isbn = r["ISBN_norm"]
        row = r.to_dict()
        row["ISBN"] = isbn
        best[isbn] = pick_better_row(best.get(isbn), row)

    return best


def write_best_map(best_map, output_csv):
    """
    Overwrite output_csv with 1 row per ISBN (best row only).
    """
    rows = list(best_map.values())
    df = pd.DataFrame(rows)

    cols = ["ISBN", "detail_url", "subjects", "summary", "status"]
    for c in cols:
        if c not in df.columns:
            df[c] = None

    df = df[cols].sort_values("ISBN")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, sep=";", index=False)


def should_retry(existing_row: dict) -> bool:
    if not existing_row:
        return True

    status = str(existing_row.get("status", "")).strip().lower()
    subjects = existing_row.get("subjects")
    summary = existing_row.get("summary")

    has_subjects = isinstance(subjects, str) and subjects.strip() != ""
    has_summary = isinstance(summary, str) and summary.strip() != ""

    if status == "no_results":
        return False
    if status in {"timeout", "security_check_failed", "found_but_empty"}:
        return True
    if status.startswith("error:"):
        return True
    if status == "ok" and not (has_subjects or has_summary):
        return True

    return False


def scrape_one_isbn(page, isbn_norm: str) -> dict:
    search_url = (
        f"{BASE}/cgi-bin/koha/opac-search.pl"
        f"?advsearch=1&idx=nb&q={isbn_norm}&weight_search=on&do=Search&sort_by=relevance"
    )

    page.goto(search_url, wait_until="domcontentloaded", timeout=SEARCH_TIMEOUT)

    block_tries = 0
    while is_block_page(page.content().lower()):
        block_tries += 1
        print(f"BLOCKED ({block_tries}/{MAX_BLOCK_RETRIES}). Solve in browser window.")
        input("After solving it, press ENTER to retry...")

        page.goto(search_url, wait_until="domcontentloaded", timeout=SEARCH_TIMEOUT)

        if block_tries >= MAX_BLOCK_RETRIES:
            return {
                "ISBN": isbn_norm,
                "detail_url": page.url,
                "subjects": None,
                "summary": None,
                "status": "security_check_failed",
            }

    first = page.locator('a.title[href*="opac-detail.pl"]').first
    if first.count() == 0:
        first = page.locator('a[href*="opac-detail.pl"]').first

    if first.count() == 0:
        return {
            "ISBN": isbn_norm,
            "detail_url": page.url,
            "subjects": None,
            "summary": None,
            "status": "no_results",
        }

    first.click(timeout=CLICK_TIMEOUT)
    page.wait_for_load_state("domcontentloaded", timeout=CLICK_TIMEOUT)

    try:
        page.wait_for_selector(
            "span.results_summary.subjects, span.results_summary.summary",
            timeout=DETAIL_WAIT_TIMEOUT,
        )
    except Exception:
        pass

    detail_url = page.url
    html = page.content()
    subjects, summary = extract_subjects_and_summary(html)

    status = "ok" if (subjects or summary) else "found_but_empty"

    return {
        "ISBN": isbn_norm,
        "detail_url": detail_url,
        "subjects": subjects,
        "summary": summary,
        "status": status,
    }


def main():
    input_csv = UPDATED_BOOKS_CSV
    output_csv = KOHA_ENRICHED_CSV

    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    df = safe_read_csv(input_csv, sep=",")
    if "ISBN" not in df.columns:
        raise ValueError("Input CSV must contain column 'ISBN'")

    df["ISBN_norm"] = df["ISBN"].map(clean_isbn)
    df = df.dropna(subset=["ISBN_norm"])

    isbn_list = df["ISBN_norm"].drop_duplicates().tolist()
    total = len(isbn_list)

    best_map = load_existing_best(output_csv)
    print(f"Loaded existing rows: {len(best_map)} unique ISBNs")
    print(f"Total ISBNs to consider: {total}")

    updates_since_save = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
            )
        )
        page = context.new_page()

        print("Browser opened. Waiting 5 seconds before starting scraping...")
        time.sleep(5)

        for idx, isbn in enumerate(isbn_list, start=1):
            old_row = best_map.get(isbn)

            if old_row and not should_retry(old_row):
                print(f"[{idx}/{total}] Skipping (already good) {isbn}")
                continue

            print(f"[{idx}/{total}] Scraping {isbn}")

            try:
                row = scrape_one_isbn(page, isbn)
            except PlaywrightTimeoutError:
                row = {"ISBN": isbn, "detail_url": None, "subjects": None, "summary": None, "status": "timeout"}
            except Exception as e:
                row = {"ISBN": isbn, "detail_url": None, "subjects": None, "summary": None, "status": f"error:{type(e).__name__}"}

            best_map[isbn] = pick_better_row(best_map.get(isbn), row)
            updates_since_save += 1

            if updates_since_save >= SAVE_EVERY:
                write_best_map(best_map, output_csv)
                print(f"Saved unique-best checkpoint -> {output_csv}")
                updates_since_save = 0

            time.sleep(SLEEP_BETWEEN)

        write_best_map(best_map, output_csv)
        print(f"Final saved unique-best -> {output_csv}")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
