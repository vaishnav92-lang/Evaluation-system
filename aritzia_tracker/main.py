#!/usr/bin/env python3
"""Aritzia Price Tracker — checks watched products and sends email alerts on price drops."""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from scraper import scrape_product
from storage import update_price
from notifier import send_price_drop_email

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

WATCHLIST_PATH = Path(__file__).parent / "watchlist.txt"


def load_watchlist(path: Path = WATCHLIST_PATH) -> list[str]:
    """Read product URLs from the watchlist file, one per line."""
    if not path.exists():
        logger.error("Watchlist not found: %s", path)
        return []

    urls = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def check_product(url: str) -> None:
    """Scrape a single product and send an alert if the price dropped."""
    logger.info("Checking: %s", url)

    try:
        product = scrape_product(url)
    except RuntimeError:
        logger.exception("Failed to scrape %s — skipping", url)
        return

    previous_price = update_price(
        url=product.url,
        name=product.name,
        price=product.current_price,
    )

    if previous_price is None:
        logger.info(
            "First time seeing %s — recorded at $%.2f",
            product.name,
            product.current_price,
        )
        return

    if product.current_price < previous_price:
        logger.info(
            "Price drop for %s: $%.2f → $%.2f",
            product.name,
            previous_price,
            product.current_price,
        )
        send_price_drop_email(
            product_name=product.name,
            old_price=previous_price,
            new_price=product.current_price,
            url=product.url,
        )
    elif product.current_price > previous_price:
        logger.info(
            "Price increase for %s: $%.2f → $%.2f",
            product.name,
            previous_price,
            product.current_price,
        )
    else:
        logger.info(
            "No change for %s — still $%.2f",
            product.name,
            product.current_price,
        )


def main() -> None:
    urls = load_watchlist()
    if not urls:
        logger.error("No URLs to track. Add product URLs to watchlist.txt.")
        sys.exit(1)

    logger.info("Tracking %d product(s)...", len(urls))

    for url in urls:
        check_product(url)

    logger.info("Done.")


if __name__ == "__main__":
    main()
