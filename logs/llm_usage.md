# LLM Usage Log

## Q1
**Question:** Why can't I scrape data from the opac using BeautifulSoup or Scrapy? <br/>
**Answer:** This is because OPAC has a security page check, and BeautifulSoup or Scrapy scrape the page that first shows up and there is no delay or wait in that. Playwright solves this problem by opening a browser window which executes Javascript and waits for the page to fully load, and allowing you to bypass the security check. After that page data is scraped using BeautifulSoup.

---
## Q2
**Question:** 
**Answer:**