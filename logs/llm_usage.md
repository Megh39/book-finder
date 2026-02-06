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

## Q20
**Question:** What would be good options for retrieving books based on a given query.
**Answer:** Best option would be to use sentence transformers, as they are built for this exact task. 

---

## Q21
Question: Other options than transformers?
Answer: Other embedding options exist such as TF-IDF and word2vec, but they rely on token overlap or shallow semantics and perform poorly for natural language matching. Local LLMs can also be used to generate embeddings, but they are resource-heavy, less deterministic, and harder to evaluate consistently. Transformer-based sentence embeddings provide the best tradeoff between semantic quality, stability, and efficiency.

---

## Q22
Question: Why use BM25?
Answer: BM25 is used to handle exact keyword and token-based matching efficiently. It performs well for short, specific, or technical queries where lexical overlap matters. In this system, BM25 is used to shortlist candidate documents before applying semantic reranking, improving both precision and performance.

---

## Q23
Question: What are the options to host the application?
Answer: Common hosting options include Render, Vercel, Railway, and Streamlit Community Cloud. Each platform offers different tradeoffs in terms of resource limits, deployment complexity, and cost.

---

## Q24
Question: Why not use Render if it runs out of RAM?
Answer: Render free tiers often have strict RAM limits, which are insufficient for loading embedding models and large NumPy arrays. Streamlit Community Cloud is better suited here because it hosts both the frontend and backend logic together and provides enough memory for embedding-based search workloads.

---

## Q25
Question: How does Streamlit help in this project?
Answer: Streamlit simplifies deployment by combining UI rendering and backend execution in a single process. It removes the need for a separate frontend-backend architecture, supports caching of heavy objects like models and embeddings, and allows rapid deployment via GitHub integration.

---

## Q26
Question: Why precompute embeddings instead of generating them at query time?
Answer: Precomputing embeddings avoids repeated encoding of the entire dataset, significantly reducing latency and compute cost. At query time, only the user query is embedded, making the system fast and scalable for read-heavy workloads.

---

## Q27
Question: Why not directly use a database full-text search?
Answer: Traditional database full-text search relies on lexical matching and cannot capture semantic similarity. Semantic embeddings allow retrieval based on meaning rather than exact word overlap, enabling natural language queries that traditional full-text search cannot handle.

---