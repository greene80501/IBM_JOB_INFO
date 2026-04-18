"""Configuration constants for the IBM Careers scraper."""

from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Listing API used by IBM careers search page.
SEARCH_API_URL = "https://www-api.ibm.com/search/api/v2"
SEARCH_PAGE_SIZE = 30

# Search filters: US + Entry Level + Internship
SEARCH_TYPES = ("Entry Level", "Internship")
SEARCH_COUNTRY = "United States"

# Output
OUTPUT_JSON = DATA_DIR / "ibm_jobs.json"
STUBS_JSON = DATA_DIR / "job_stubs.json"

# Scraping performance settings
HEADLESS = True
DETAIL_WORKERS = 8
PAGE_GOTO_TIMEOUT = 60_000
DETAIL_WAIT_AFTER_LOAD_MS = 700
CACHE_TTL_DAYS = 14
