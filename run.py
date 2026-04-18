"""Entry point for IBM careers scrape."""

import argparse
import asyncio

from config import DETAIL_WORKERS
from scraper.ibm_scraper import scrape_jobs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IBM careers scraper")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore cached job details and re-scrape every detail page.",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Optional cap for jobs to fetch (useful for quick tests).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DETAIL_WORKERS,
        help="Concurrent detail-page workers.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    print("=" * 60)
    print("IBM Careers Scraper - Fast Mode (US Entry Level + Internship)")
    print("=" * 60)
    await scrape_jobs(
        force_refresh=args.force_refresh,
        max_jobs=args.max_jobs,
        detail_workers=max(1, args.workers),
    )


if __name__ == "__main__":
    asyncio.run(main())
