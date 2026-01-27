# LLM Usage Log

## Q1
**Question:** Why can't I scrape data from the opac using BeautifulSoup or Scrapy? <br/>
**Answer:** This is because OPAC has a security page check, and BeautifulSoup or Scrapy scrape the page that first shows up and there is no delay or wait in that. Playwright solves this problem by opening a browser window which executes Javascript and waits for the page to fully load, and allowing you to bypass the security check. After that page data is scraped using BeautifulSoup.

---
## Q2
**Question:** I can't run the scraper continuously as I have to shut down the laptop in between. <br/>
**Answer:** Updated the scraper to support resume by checking existing output CSV before scraping again, saving progress at fixed intervals.

---
## Q3
**Question:** Should I hit multiple endpoints or a single endpoint in OpenLibrary?  
**Answer:** Multiple endpoints. Flow is: `/isbn/{isbn}.json` (edition) → `/authors/{id}.json` (author names) → `/works/{id}.json` (subjects + better description).

---

## Q4
**Question:** Same fix as OPAC to continue running OpenLibrary from previous progress?  
**Answer:** Added resume support using `row_id` by loading already processed `row_id`s from the output CSV and skipping them on rerun, while saving results every fixed number of rows.

---

## Q5
**Question:** How to search in OpenAlex when ISBNs aren’t available?  
**Answer:** Search OpenAlex using the **Title**, compute similarity score with the returned candidates, accept only high-confidence matches, and store a status like `ok_exact_title`, `ok_high_confidence`, or `rejected_low_confidence`.

---

## Q6
**Question:** Merge logic for the final dataset?  
**Answer:** Merge OPAC (Koha) + OpenLibrary using **ISBN**, and merge OpenAlex using **normalized Title match** (title_key + similarity best-row selection).

---

## Q7
**Question:** Some rows in OPAC output are duplicated. Why?  
**Answer:** Because the scraper appends rows every time you retry an ISBN manually or rerun the script, so multiple attempts create duplicate ISBN rows in the output log.

---

## Q8
**Question:** Error in years where min was 0 and max was 2090.  
**Answer:** Apply a year range filter (example: keep only 1800–2026) and set out-of-range values to `None` before loading into the database.

---

# Other Fixes (Not Visible in Final Output)

## Q9
**Question:** Due to script changes, CSV structure got messed up. How to fix?  
**Answer:** Split the corrupted CSV into multiple clean files, normalize headers/columns, and rebuild a consistent final CSV from the repaired outputs.

---

## Q10
**Question:** OpenAlex abstract mismatch with title. Why?  
**Answer:** Because OpenAlex was previously merged using `row_id`, but `row_id` was manually generated and not stable across datasets. Fix was to merge OpenAlex using normalized Title instead.

---

## Q11
**Question:** Should we use Google Books API or not?  
**Answer:** For large-scale enrichment, using an API key is recommended, but it can become paid/limited at scale, so it was avoided for this project.

---

## Q12
**Question:** Some rows are being skipped in Koha scraper when resuming.  
**Answer:** Add a delay before scraping starts and ensure resume logic only skips rows that are actually “complete”, not rows that failed due to timeout/security checks.

---

## Q13
**Question:** Use AccessionID as a primary key or not?
**Answer:** No, because AccessionID was unique in the original database and we have removed the duplicate books where either Editions or Titles were removed. Hence a manual row ID was created.

---

## Q14
**Question:** Write a script to scrape data from OPAC (Koha).  
**Answer:** Provided a Playwright + BeautifulSoup scraper that searches OPAC by ISBN, opens the first result, then extracts subjects + summary from the detail page.

---

## Q15
**Question:** Why should the API not use `DB_FILE = "../storage/books.db"`?  
**Answer:** Relative paths depend on where the server is started from. Using absolute path based on `__file__` makes it reliable no matter where uvicorn runs.

---

## Q16
**Question:** Write a script to execute pipeline on windows and ubuntu.
**Answer:** Provided 2 scripts for execution on windows and Ubuntu.

---

## Q17
**Question:** Why is my config file not working?
**Answer:** Added path fix by adding a pointer to root directory so that config file is accessible from anywhere.

---
## Q18 
**Question:** Write a script to call API of openlibrary.
**Answer**: Script which goes through multiple endpoints(work,edition) and provides final output.

---

## Q19
**Question:** Write a script to call API of Openalex.
**Answer:** Script which goes through OpenAlex data and returns results based on title similarity.

---
