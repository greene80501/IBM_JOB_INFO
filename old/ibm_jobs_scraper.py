#!/usr/bin/env python3
"""
IBM Careers Scraper — Clean Edition

Scrapes IBM careers search results and every individual job posting,
then deeply cleans and structures the data:
  • Removes verbose keys and prefixes
  • Parses salaries into raw integers
  • Parses dates into ISO-8601
  • Splits locations into clean arrays
  • Detects section headers (About Business Unit, Your Life @ IBM, etc.)
  • Normalizes whitespace and fixes encoding artifacts

Example usage:
    python ibm_jobs_scraper.py --limit-jobs 10 --output-json ibm_jobs.json
"""

import argparse
import asyncio
import csv
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright, Browser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text cleaning utilities
# ---------------------------------------------------------------------------

_RE_SALARY = re.compile(r"[\$,]")
_RE_WHITESPACE = re.compile(r"\n{3,}")
_RE_BULLET_EMPTY = re.compile(r"\n\s*•\s*\n")
_ENCODING_MAP = str.maketrans({
    "\u2019": "'",   # right single quote
    "\u2018": "'",   # left single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u00a0": " ",   # non-breaking space
})


def clean_text(text: str) -> str:
    """Normalize whitespace, strip empty bullets, and fix common encoding artifacts."""
    if not text:
        return ""
    text = text.translate(_ENCODING_MAP)
    # Replace literal replacement-char diamonds with apostrophe or space
    text = text.replace("�", "'")
    # Collapse more than 2 newlines
    text = _RE_WHITESPACE.sub("\n\n", text)
    text = _RE_BULLET_EMPTY.sub("\n", text)
    return text.strip()


def parse_salary(value: str) -> Optional[int]:
    """Convert '100,800.00' → 100800."""
    if not value:
        return None
    cleaned = _RE_SALARY.sub("", value.split(".")[0])
    cleaned = cleaned.strip()
    try:
        return int(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_date(value: str) -> Optional[str]:
    """Convert '21-Nov-2025' → '2025-11-21'."""
    if not value:
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_boolean(value: str) -> Optional[bool]:
    v = value.strip().lower()
    if v in ("yes", "y", "true", "1"):
        return True
    if v in ("no", "n", "false", "0", ""):
        return False
    return None


def split_list(value: str) -> List[str]:
    """Split a comma-separated location string into a clean, title-cased list."""
    if not value:
        return []
    parts = [p.strip().title() for p in value.split(",") if p.strip()]
    return parts


# ---------------------------------------------------------------------------
# Main search page parser
# ---------------------------------------------------------------------------

class MainPageParser:
    """Parser specific to the IBM careers search results main page."""

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")

    def parse_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        cards = self.soup.find_all("a", class_="bx--card-group__card")
        for card in cards:
            href = card.get("href", "")
            if "JobDetail" not in href:
                continue

            job_id = self._extract_job_id(href)
            eyebrow = card.find("div", class_="bx--card__eyebrow")
            heading = card.find("div", class_="bx--card__heading")
            copy_inner = card.find("div", class_="ibm--card__copy__inner") or card.find("div", class_="bx--card__copy")

            level = ""
            location = ""
            if copy_inner:
                parts = [p.strip() for p in copy_inner.stripped_strings]
                if len(parts) >= 2:
                    level, location = parts[0], parts[1]
                elif len(parts) == 1:
                    level = parts[0]

            jobs.append({
                "id": job_id,
                "title": clean_text(heading.get_text(strip=True)) if heading else "",
                "category": clean_text(eyebrow.get_text(strip=True)) if eyebrow else "",
                "career_level": clean_text(level),
                "location_summary": clean_text(location),
                "url": href,
            })
        return jobs

    def get_total_items_text(self) -> str:
        elem = self.soup.find("div", class_="ibm--totalresults__totalresults")
        return elem.get_text(strip=True) if elem else ""

    def get_current_page(self) -> int:
        active = self.soup.find("a", class_="cds--pagination-nav__page--active")
        if active:
            text = active.get_text(strip=True)
            if text.isdigit():
                return int(text)
        return 1

    def get_total_pages(self) -> int:
        text = self.get_total_items_text()
        m = re.search(r"of\s+(\d+)\s+items", text)
        if m:
            return max(1, (int(m.group(1)) + 29) // 30)
        pages = self.soup.find_all("a", class_="cds--pagination-nav__page")
        numbers = [int(p.get_text(strip=True)) for p in pages if p.get_text(strip=True).isdigit()]
        return max(numbers) if numbers else 1

    @staticmethod
    def _extract_job_id(href: str) -> str:
        return parse_qs(urlparse(href).query).get("jobId", [""])[0]


# ---------------------------------------------------------------------------
# Job detail page parser
# ---------------------------------------------------------------------------

class JobDetailParser:
    """Parser specific to an IBM careers JobDetail posting page."""

    # Map labeled field names → clean keys
    LABEL_MAP = {
        "introduction": "intro",
        "your role and responsibilities": "responsibilities",
        "required education": "edu_required",
        "preferred education": "edu_preferred",
        "required technical and professional expertise": "skills_required",
        "preferred technical and professional experience": "skills_preferred",
        "job title": "official_title",
        "date posted": "posted_at",
        "job id": None,          # redundant; we already have it from search page
        "city / township / village": "cities",
        "state / province": "states",
        "country": "country",
        "work arrangement": "work_type",
        "area of work": "department",
        "employment type": "employment_type",
        "contract type": "contract_type",
        "projected minimum salary per year": "salary_min",
        "projected maximum salary per year": "salary_max",
        "position type": "career_level",
        "travel required": "travel",
        "company": "company",
        "shift": "shift",
        "is this role a commissionablesales incentive based position": "commission_role",
        "is this role a commissionable/sales incentive based position": "commission_role",
    }

    @staticmethod
    def _normalize_label(raw: str) -> str:
        """Strip punctuation and extra spaces from a field label for lookup."""
        return re.sub(r"[^a-z0-9\s]+", "", raw).strip()

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")

    def parse(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Returns (cleaned_data, error_message).
        If the page is a 406 or other error, error_message is set.
        """
        title_tag = self.soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else ""
        if "406" in page_title or "Not Acceptable" in page_title:
            return {}, "406 Not Acceptable"

        data: Dict[str, Any] = {}

        # Walk through the article content in document order
        # The IBM detail page has fields inside <article class="article--details">,
        # but some are siblings of the top <article>, so we walk the whole document
        # starting from the main content section.
        root = self.soup.find("main") or self.soup.find("section", class_="js_views") or self.soup
        if not root:
            return {}, "No root container found"

        current_section = ""
        current_field = ""

        # Gather all relevant elements in document order
        fields = root.find_all("div", class_="article__content__view__field")
        headers = root.find_all("summary", class_="article__header")
        elems = sorted(fields + headers, key=lambda e: e.sourceline if e.sourceline else 0)

        for elem in elems:
            if elem.name == "summary" and "article__header" in (elem.get("class") or []):
                h3 = elem.find("h3")
                current_section = h3.get_text(strip=True).upper() if h3 else ""
                continue

            if "article__content__view__field" not in (elem.get("class") or []):
                continue

            label_div = elem.find("div", class_="article__content__view__field__label")
            value_div = elem.find("div", class_="article__content__view__field__value")

            if label_div and value_div:
                raw_label = label_div.get_text(separator=" ", strip=True).lower()
                current_field = raw_label
                lookup_label = self._normalize_label(raw_label)
                clean_key = self.LABEL_MAP.get(lookup_label)
                if clean_key is None:
                    continue  # skip redundant fields
                raw_value = value_div.get_text(separator="\n", strip=True)
                data[clean_key] = self._coerce(clean_key, clean_text(raw_value))

            elif value_div:
                raw_value = clean_text(value_div.get_text(separator="\n", strip=True))
                if not raw_value:
                    continue
                key = self._assign_unlabeled(current_section, current_field, raw_value, data)
                if key:
                    existing = data.get(key, "")
                    if existing:
                        data[key] = f"{existing}\n\n{raw_value}"
                    else:
                        data[key] = raw_value

        # Post-process: ensure lists are arrays even if empty
        for list_key in ("cities", "states"):
            if list_key not in data:
                data[list_key] = []

        return data, None

    def _coerce(self, key: str, value: str) -> Any:
        if not value:
            return None
        if key == "salary_min":
            return parse_salary(value)
        if key == "salary_max":
            return parse_salary(value)
        if key == "posted_at":
            return parse_date(value)
        if key == "commission_role":
            return parse_boolean(value)
        if key in ("cities", "states"):
            return split_list(value)
        if key == "company":
            # Strip numeric prefix like "(0147) International Business Machines Corporation"
            value = re.sub(r"^\(\d+\)\s*", "", value).strip()
            return value
        return value

    def _assign_unlabeled(self, section: str, last_label: str, value: str, data: Dict[str, Any]) -> Optional[str]:
        """Decide which clean key an unlabeled text block belongs to."""
        section = section.upper()
        lower_val = value.lower()

        if section == "ABOUT BUSINESS UNIT":
            return "about_business"

        if section == "YOUR LIFE @ IBM":
            return "life_at_ibm"

        if section == "ABOUT IBM":
            # Usually two blocks: general IBM description and EEO statement
            if "equal-opportunity employer" in lower_val or "equal opportunity" in lower_val:
                return "equal_opportunity"
            return "about_ibm"

        if section == "OTHER RELEVANT JOB DETAILS":
            if "benefits program" in lower_val or "healthcare benefits" in lower_val:
                return "benefits"
            if "visa sponsorship" in lower_val:
                return "visa_policy"
            if "compensation range" in lower_val or "salary will vary" in lower_val:
                return "compensation_policy"
            # fallback: append to a generic note if we can't classify
            return "other_notes"

        # Fallback for any stray unlabeled block before the first header
        return "extra_content"


# ---------------------------------------------------------------------------
# Scraper orchestrator
# ---------------------------------------------------------------------------

class IBMJobScraper:
    def __init__(
        self,
        start_url: str,
        output_json: str = "ibm_jobs.json",
        output_csv: str = "ibm_jobs.csv",
        limit_pages: Optional[int] = None,
        limit_jobs: Optional[int] = None,
        delay_seconds: float = 0.8,
        concurrency: int = 6,
    ):
        self.start_url = start_url
        self.output_json = output_json
        self.output_csv = output_csv
        self.limit_pages = limit_pages
        self.limit_jobs = limit_jobs
        self.delay_seconds = delay_seconds
        self.concurrency = concurrency
        self.all_jobs: List[Dict[str, Any]] = []

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                await self._scrape_main_pages(browser)
                await self._scrape_job_details(browser)
                self._save_results()
            finally:
                await browser.close()

    async def _scrape_main_pages(self, browser: Browser):
        page = await browser.new_page()
        logger.info("Loading main search page: %s", self.start_url)
        await page.goto(self.start_url, wait_until="load", timeout=120000)
        await page.wait_for_selector(".bx--card-group__card", timeout=30000)
        await asyncio.sleep(3)

        current_page = 1
        while True:
            html = await page.content()
            parser = MainPageParser(html)

            total_text = parser.get_total_items_text()
            total_pages = parser.get_total_pages()
            page_num = parser.get_current_page()
            jobs = parser.parse_jobs()

            logger.info(
                "Main page %s/%s (%s) – found %s jobs",
                page_num, total_pages, total_text, len(jobs),
            )

            for job in jobs:
                if not any(j["id"] == job["id"] for j in self.all_jobs):
                    self.all_jobs.append(job)

            if self.limit_pages and current_page >= self.limit_pages:
                logger.info("Reached page limit (%s)", self.limit_pages)
                break

            if page_num >= total_pages:
                logger.info("Reached last page")
                break

            nxt = page_num + 1
            next_link = page.locator(f"a.cds--pagination-nav__page >> text={nxt}")
            try:
                await next_link.click(timeout=10000)
                await page.wait_for_timeout(4000)
                current_page += 1
            except Exception as exc:
                logger.error("Failed to click page %s: %s", nxt, exc)
                break

        await page.close()
        logger.info("Total unique jobs collected: %s", len(self.all_jobs))

    async def _scrape_job_details(self, browser: Browser):
        jobs_to_scrape = self.all_jobs[: self.limit_jobs] if self.limit_jobs else self.all_jobs
        semaphore = asyncio.Semaphore(self.concurrency)

        async def scrape_one(job: Dict, idx: int):
            async with semaphore:
                url = job.get("url", "")
                if not url:
                    return

                logger.info(
                    "Scraping detail %s/%s – ID %s – %s",
                    idx, len(jobs_to_scrape), job["id"], job["title"],
                )

                page = await browser.new_page()
                try:
                    await page.goto(url, wait_until="load", timeout=120000)
                    await page.wait_for_timeout(2500)
                    html = await page.content()
                    parser = JobDetailParser(html)
                    details, err = parser.parse()
                    if err:
                        job["detail_error"] = err
                        logger.warning("Job %s detail error: %s", job["id"], err)
                    else:
                        job.update(details)
                except Exception as exc:
                    logger.exception("Error scraping job %s: %s", job["id"], exc)
                    job["detail_error"] = str(exc)
                finally:
                    await page.close()

                if self.delay_seconds > 0:
                    await asyncio.sleep(self.delay_seconds)

        await asyncio.gather(
            *[scrape_one(job, i + 1) for i, job in enumerate(jobs_to_scrape)]
        )

    def _save_results(self):
        # JSON: clean nested structure (details merged into top level as requested)
        with open(self.output_json, "w", encoding="utf-8") as f:
            json.dump(self.all_jobs, f, indent=2, ensure_ascii=False)
        logger.info("Saved JSON: %s", self.output_json)

        # CSV: flatten arrays to pipe-separated strings for readability
        if self.all_jobs:
            rows = []
            all_keys = set()
            for job in self.all_jobs:
                row = {}
                for k, v in job.items():
                    if isinstance(v, list):
                        row[k] = " | ".join(v) if v else ""
                    elif v is None:
                        row[k] = ""
                    else:
                        row[k] = v
                rows.append(row)
                all_keys.update(row.keys())

            # Desired column order
            priority = [
                "id", "title", "official_title", "category", "career_level",
                "department", "location_summary", "cities", "states", "country",
                "work_type", "employment_type", "contract_type", "shift",
                "travel", "company", "commission_role", "salary_min", "salary_max",
                "posted_at", "url", "detail_error",
                "intro", "responsibilities", "skills_required", "skills_preferred",
                "edu_required", "edu_preferred",
                "about_business", "life_at_ibm", "about_ibm", "equal_opportunity",
                "benefits", "visa_policy", "compensation_policy", "other_notes",
                "extra_content",
            ]
            fieldnames = [k for k in priority if k in all_keys]
            fieldnames += sorted(all_keys - set(fieldnames))

            with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            logger.info("Saved CSV: %s", self.output_csv)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape IBM Careers job listings")
    parser.add_argument(
        "--url",
        default="https://www.ibm.com/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_18[1]=Internship&field_keyword_05[0]=United%20States",
        help="IBM careers search URL to start from",
    )
    parser.add_argument("--output-json", default="ibm_jobs.json", help="Output JSON file")
    parser.add_argument("--output-csv", default="ibm_jobs.csv", help="Output CSV file")
    parser.add_argument("--limit-pages", type=int, default=None, help="Max search pages")
    parser.add_argument("--limit-jobs", type=int, default=None, help="Max job details")
    parser.add_argument("--delay", type=float, default=0.8, help="Delay between requests")
    parser.add_argument("--concurrency", type=int, default=6, help="Concurrent detail tabs")
    return parser


def main():
    args = build_parser().parse_args()
    scraper = IBMJobScraper(
        start_url=args.url,
        output_json=args.output_json,
        output_csv=args.output_csv,
        limit_pages=args.limit_pages,
        limit_jobs=args.limit_jobs,
        delay_seconds=args.delay,
        concurrency=args.concurrency,
    )
    asyncio.run(scraper.run())


if __name__ == "__main__":
    main()
