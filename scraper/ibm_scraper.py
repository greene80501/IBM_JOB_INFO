"""Fast IBM careers scraper with API listing + concurrent detail extraction."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib import request

from playwright.async_api import BrowserContext, async_playwright
from playwright_stealth import Stealth

from config import (
    CACHE_TTL_DAYS,
    DETAIL_WAIT_AFTER_LOAD_MS,
    DETAIL_WORKERS,
    HEADLESS,
    OUTPUT_JSON,
    PAGE_GOTO_TIMEOUT,
    SEARCH_API_URL,
    SEARCH_COUNTRY,
    SEARCH_PAGE_SIZE,
    SEARCH_TYPES,
    STUBS_JSON,
)

_US_STATES = {
    "alabama",
    "alaska",
    "arizona",
    "arkansas",
    "california",
    "colorado",
    "connecticut",
    "delaware",
    "florida",
    "georgia",
    "hawaii",
    "idaho",
    "illinois",
    "indiana",
    "iowa",
    "kansas",
    "kentucky",
    "louisiana",
    "maine",
    "maryland",
    "massachusetts",
    "michigan",
    "minnesota",
    "mississippi",
    "missouri",
    "montana",
    "nebraska",
    "nevada",
    "new hampshire",
    "new jersey",
    "new mexico",
    "new york",
    "north carolina",
    "north dakota",
    "ohio",
    "oklahoma",
    "oregon",
    "pennsylvania",
    "rhode island",
    "south carolina",
    "south dakota",
    "tennessee",
    "texas",
    "utah",
    "vermont",
    "virginia",
    "washington",
    "west virginia",
    "wisconsin",
    "wyoming",
    "district of columbia",
}

_TRACKING_HOSTS = (
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "trustarc.com",
    "demandbase.com",
)
_STEALTH = Stealth()


def extract_job_id_from_href(href: str) -> str:
    match = re.search(r"[?&]jobId=(\d+)", href or "")
    return match.group(1) if match else ""


def normalize_detail_url(href: str) -> str:
    if not href:
        return href
    if "source=" in href:
        return href
    separator = "&" if "?" in href else "?"
    return f"{href}{separator}source=WEB_Search_NA"


def parse_location(raw: str) -> list[str]:
    if not raw or raw.lower() == "multiple cities":
        return []
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) >= 3 and parts[-1].strip().lower() == "united states":
        candidates = parts[:-2]
        cities = [c.title() for c in candidates if c.strip().lower() not in _US_STATES]
        return cities if cities else [candidates[0].title()]
    if parts:
        return [parts[0].title()]
    return []


def clean_description(body_text: str) -> str:
    lines = [ln.strip() for ln in body_text.splitlines()]
    start_idx = 0
    for idx, line in enumerate(lines):
        if line == "Apply now":
            start_idx = idx + 1
            break
    cleaned = []
    for line in lines[start_idx:]:
        if line in ("Email", "X", "LinkedIn", "Apply now"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def extract_salary_fields(lines: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"salary_min": None, "salary_max": None, "pay_range": None}
    for idx, line in enumerate(lines):
        if "Projected Minimum Salary per year" in line and idx + 1 < len(lines):
            result["salary_min"] = lines[idx + 1].strip()
        if "Projected Maximum Salary per year" in line and idx + 1 < len(lines):
            result["salary_max"] = lines[idx + 1].strip()

    if result["salary_min"] and result["salary_max"]:
        result["pay_range"] = f"${result['salary_min']} - ${result['salary_max']} per year"
    elif result["salary_min"]:
        result["pay_range"] = f"${result['salary_min']}+ per year"
    elif result["salary_max"]:
        result["pay_range"] = f"Up to ${result['salary_max']} per year"
    return result


def extract_labeled_value(lines: list[str], label: str) -> str | None:
    label_lower = label.lower().strip()
    blockers = {"date posted", "required education", "preferred education"}
    for idx, line in enumerate(lines):
        if line.lower().strip() == label_lower:
            for look_ahead in range(idx + 1, min(idx + 5, len(lines))):
                value = lines[look_ahead].strip()
                if not value:
                    continue
                if value.lower().strip() in blockers:
                    break
                return value
    return None


def extract_type_from_lines(lines: list[str]) -> str:
    for line in lines[:25]:
        if line in SEARCH_TYPES:
            return line
    return ""


def _build_search_payload(offset: int, size: int) -> dict[str, Any]:
    return {
        "appId": "careers",
        "scopes": ["careers2"],
        "query": {"bool": {"must": []}},
        "post_filter": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [{"term": {"field_keyword_18": SEARCH_TYPES[0]}}, {"term": {"field_keyword_18": SEARCH_TYPES[1]}}]
                        }
                    },
                    {"term": {"field_keyword_05": SEARCH_COUNTRY}},
                ]
            }
        },
        "size": size,
        "from": offset,
        "sort": [{"_score": "desc"}, {"pageviews": "desc"}],
        "lang": "zz",
        "localeSelector": {},
        "sm": {"query": "", "lang": "zz"},
        "_source": [
            "_id",
            "title",
            "url",
            "description",
            "language",
            "entitled",
            "field_keyword_17",
            "field_keyword_08",
            "field_keyword_18",
            "field_keyword_19",
        ],
    }


def fetch_listing_page(offset: int, size: int) -> tuple[int, list[dict[str, Any]]]:
    payload = _build_search_payload(offset, size)
    req = request.Request(
        SEARCH_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", "accept": "application/json"},
    )
    with request.urlopen(req, timeout=40) as response:
        body = json.loads(response.read().decode("utf-8"))
    total = int(body["hits"]["total"]["value"])
    hits = body["hits"]["hits"]
    return total, hits


def fetch_all_listings(max_jobs: int | None = None) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    seen: set[str] = set()
    offset = 0
    total = None

    while True:
        api_total, hits = fetch_listing_page(offset=offset, size=SEARCH_PAGE_SIZE)
        total = api_total if total is None else total
        if not hits:
            break

        for hit in hits:
            source = hit.get("_source", {})
            detail_url = normalize_detail_url(source.get("url", ""))
            job_id = extract_job_id_from_href(detail_url)
            if not job_id or job_id in seen:
                continue
            location_raw = source.get("field_keyword_19", "").replace(", US", ", United States")
            if location_raw == "Multiple Cities, United States":
                location_raw = "Multiple Cities"

            jobs.append(
                {
                    "job_id": job_id,
                    "title": source.get("title", "").strip(),
                    "team": source.get("field_keyword_08", "").strip(),
                    "type": source.get("field_keyword_18", "").strip(),
                    "location_raw": location_raw.strip(),
                    "detail_url": detail_url,
                }
            )
            seen.add(job_id)
            if max_jobs and len(jobs) >= max_jobs:
                return jobs

        offset += SEARCH_PAGE_SIZE
        if offset >= total:
            break

    return jobs


def load_existing_jobs() -> dict[str, dict[str, Any]]:
    if not OUTPUT_JSON.exists():
        return {}
    try:
        rows = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        jid = str(row.get("job_id", "")).strip()
        if jid:
            by_id[jid] = row
    return by_id


def _parse_scraped_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def should_refresh(stub: dict[str, Any], existing: dict[str, Any] | None, force_refresh: bool) -> bool:
    if force_refresh or not existing:
        return True

    if (stub.get("detail_url") or "") != (existing.get("detail_url") or ""):
        return True

    required_fields = ("description", "date_posted", "required_education", "salary_min", "salary_max")
    if any(not existing.get(field) for field in required_fields):
        return True

    scraped_at = _parse_scraped_at(existing.get("scraped_at"))
    if not scraped_at:
        return True
    return scraped_at < datetime.now(timezone.utc) - timedelta(days=CACHE_TTL_DAYS)


def _job_quality(job: dict[str, Any] | None) -> int:
    if not job:
        return 0
    score = 0
    if job.get("description"):
        score += 2
    if job.get("date_posted"):
        score += 2
    if job.get("required_education"):
        score += 2
    if job.get("preferred_education"):
        score += 1
    if job.get("pay_range") or (job.get("salary_min") and job.get("salary_max")):
        score += 2
    if job.get("cities"):
        score += 1
    return score


async def _build_browser_context():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=HEADLESS)
    context = await browser.new_context(viewport={"width": 1600, "height": 1100})

    async def _route(route):
        req = route.request
        if req.resource_type in ("image", "media", "font", "stylesheet"):
            await route.abort()
            return
        if any(host in req.url for host in _TRACKING_HOSTS):
            await route.abort()
            return
        await route.continue_()

    await context.route("**/*", _route)
    return playwright, browser, context


async def _scrape_one(page, job: dict[str, Any], wait_after_load_ms: int) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, 4):
        try:
            await page.goto(job["detail_url"], wait_until="domcontentloaded", timeout=PAGE_GOTO_TIMEOUT)
            await page.wait_for_timeout(wait_after_load_ms)

            body_text = await page.inner_text("body")
            lines = [line.strip() for line in body_text.splitlines() if line.strip()]

            h2 = await page.query_selector("h2")
            if h2:
                title = (await h2.inner_text()).strip()
                if title:
                    job["title"] = title

            location_raw = job.get("location_raw", "")
            for line in lines:
                if "United States" in line and "," in line and len(line) < 140:
                    location_raw = line
                    break
            job["location_raw"] = location_raw
            job["cities"] = parse_location(location_raw)

            if not job.get("type"):
                extracted_type = extract_type_from_lines(lines)
                if extracted_type:
                    job["type"] = extracted_type

            job["date_posted"] = extract_labeled_value(lines, "Date posted")
            job["required_education"] = extract_labeled_value(lines, "Required education")
            job["preferred_education"] = extract_labeled_value(lines, "Preferred education")
            job["description"] = clean_description(body_text)
            job.update(extract_salary_fields(lines))
            job["scraped_at"] = datetime.now(timezone.utc).isoformat()

            # Retry when page clearly failed to render key details.
            if _job_quality(job) < 4:
                raise RuntimeError("detail page incomplete")
            return job
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                await page.wait_for_timeout(500 * attempt)

    job["scrape_error"] = str(last_error)
    job["scraped_at"] = datetime.now(timezone.utc).isoformat()
    return job


async def scrape_details_concurrent(
    jobs: list[dict[str, Any]],
    *,
    workers: int,
    wait_after_load_ms: int = DETAIL_WAIT_AFTER_LOAD_MS,
) -> list[dict[str, Any]]:
    if not jobs:
        return jobs

    playwright, browser, context = await _build_browser_context()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    for job in jobs:
        queue.put_nowait(job)

    out: list[dict[str, Any]] = []
    lock = asyncio.Lock()
    total = len(jobs)
    done = 0

    async def worker(worker_id: int):
        nonlocal done
        page = await context.new_page()
        await _STEALTH.apply_stealth_async(page)
        page.set_default_timeout(PAGE_GOTO_TIMEOUT)
        page.set_default_navigation_timeout(PAGE_GOTO_TIMEOUT)
        try:
            while True:
                try:
                    job = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                try:
                    updated = await _scrape_one(page, job, wait_after_load_ms=wait_after_load_ms)
                except Exception as exc:
                    updated = {**job, "scrape_error": str(exc), "scraped_at": datetime.now(timezone.utc).isoformat()}

                async with lock:
                    out.append(updated)
                    done += 1
                    if done % 10 == 0 or done == total:
                        print(f"  [Detail] {done}/{total} complete")
                queue.task_done()
        finally:
            await page.close()

    try:
        tasks = [asyncio.create_task(worker(i)) for i in range(max(1, workers))]
        await asyncio.gather(*tasks)
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

    out_by_id = {j["job_id"]: j for j in out}
    return [out_by_id.get(j["job_id"], j) for j in jobs]


def save_json(path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


async def scrape_jobs(
    *,
    force_refresh: bool = False,
    max_jobs: int | None = None,
    detail_workers: int = DETAIL_WORKERS,
) -> list[dict[str, Any]]:
    print("[Phase 1] Fetching listing stubs via API...")
    stubs = fetch_all_listings(max_jobs=max_jobs)
    print(f"[Phase 1] Collected {len(stubs)} stubs")
    save_json(STUBS_JSON, stubs)

    existing = load_existing_jobs()
    reused: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []

    for stub in stubs:
        old = existing.get(stub["job_id"])
        if should_refresh(stub, old, force_refresh=force_refresh):
            pending.append(stub)
        else:
            cached = dict(old)
            cached.update(stub)
            reused.append(cached)

    print(f"[Phase 2] Reusing {len(reused)} cached jobs, scraping {len(pending)} detail pages...")
    refreshed = await scrape_details_concurrent(pending, workers=detail_workers)

    # Recovery pass for detail pages that still look incomplete after fast mode.
    low_quality = [job for job in refreshed if _job_quality(job) < 5]
    if low_quality:
        print(f"[Phase 2] Recovery pass on {len(low_quality)} low-quality jobs (single worker)...")
        recovered = await scrape_details_concurrent(
            low_quality,
            workers=1,
            wait_after_load_ms=max(1_600, DETAIL_WAIT_AFTER_LOAD_MS),
        )
        recovered_by_id = {job["job_id"]: job for job in recovered}
        for idx, job in enumerate(refreshed):
            better = recovered_by_id.get(job["job_id"])
            if better and _job_quality(better) > _job_quality(job):
                refreshed[idx] = better

    refreshed_by_id = {job["job_id"]: job for job in refreshed}
    reused_by_id = {job["job_id"]: job for job in reused}

    rows: list[dict[str, Any]] = []
    for stub in stubs:
        jid = stub["job_id"]
        old = existing.get(jid)
        new = refreshed_by_id.get(jid) or reused_by_id.get(jid) or dict(stub)

        # Prevent regressions when a new scrape fails or has significantly less detail.
        if _job_quality(old) > _job_quality(new):
            chosen = dict(old)
            chosen.update(stub)
        else:
            chosen = dict(new)
            chosen.update({k: v for k, v in stub.items() if k in ("job_id", "detail_url", "title", "team", "type")})

        rows.append(chosen)
    save_json(OUTPUT_JSON, rows)

    with_pay = sum(1 for job in rows if job.get("pay_range"))
    with_date = sum(1 for job in rows if job.get("date_posted"))
    with_required_edu = sum(1 for job in rows if job.get("required_education"))
    print(f"[Phase 3] Wrote {len(rows)} jobs to {OUTPUT_JSON}")
    print(f"[Phase 3] Jobs with pay range: {with_pay}/{len(rows)}")
    print(f"[Phase 3] Jobs with date posted: {with_date}/{len(rows)}")
    print(f"[Phase 3] Jobs with required education: {with_required_edu}/{len(rows)}")
    return rows
