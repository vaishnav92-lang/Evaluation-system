"""Playwright-based scraper for Aritzia product pages."""

import logging
from dataclasses import dataclass
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


@dataclass
class ProductData:
    url: str
    name: str
    current_price: float
    original_price: float | None
    on_sale: bool


def _parse_price(text: str) -> float:
    """Strip currency symbols and parse a price string to float."""
    cleaned = text.strip().replace("$", "").replace(",", "")
    return float(cleaned)


def scrape_product(url: str, timeout_ms: int = 30000) -> ProductData:
    """Visit an Aritzia product page and extract pricing data.

    Args:
        url: Full Aritzia product URL or file:// path for testing.
        timeout_ms: Max time to wait for page elements in milliseconds.

    Returns:
        ProductData with extracted fields.

    Raises:
        RuntimeError: If the page fails to load or prices can't be found.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            # Aritzia is JS-heavy — wait for price elements to render.
            # For local file:// URLs this resolves instantly.
            try:
                page.wait_for_selector(
                    "[aria-label='Product Price'],"
                    "[class*='product-price'],"
                    "[class*='price'],"
                    "[data-auid='product-price']",
                    timeout=min(timeout_ms, 5000),
                )
            except PlaywrightTimeout:
                logger.debug("Price selector wait timed out — continuing with extraction")
            # Extra settle time for dynamic content (skip for local files).
            if not url.startswith("file://"):
                page.wait_for_timeout(2000)

            # --- Product name ---
            name = _extract_name(page)

            # --- Prices ---
            current_price, original_price, on_sale = _extract_prices(page)

            logger.info(
                "Scraped %s — current: $%.2f, original: %s, on_sale: %s",
                name,
                current_price,
                f"${original_price:.2f}" if original_price else "N/A",
                on_sale,
            )

            return ProductData(
                url=url,
                name=name,
                current_price=current_price,
                original_price=original_price,
                on_sale=on_sale,
            )

        except PlaywrightTimeout as exc:
            raise RuntimeError(f"Timed out loading {url}") from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to scrape {url}: {exc}") from exc
        finally:
            browser.close()


def _extract_name(page) -> str:
    """Try several selectors to grab the product name."""
    selectors = [
        "h1[class*='product-name']",
        "h1[data-auid='product-name']",
        "[aria-label='Product Name']",
        "h1",
    ]
    for sel in selectors:
        el = page.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if text:
                return text
    return "Unknown Product"


def _extract_prices(page) -> tuple[float, float | None, bool]:
    """Extract current price, original price, and sale status.

    Returns:
        (current_price, original_price_or_None, on_sale)
    """
    current_price = None
    original_price = None

    # Strategy 1: Look for sale price + regular price pair.
    sale_selectors = [
        "[class*='sale-price']",
        "[class*='special-price']",
        "[aria-label*='Sale']",
        "[aria-label*='sale']",
        "span.product-price--sale",
    ]
    regular_selectors = [
        "[class*='regular-price']",
        "[class*='original-price']",
        "s",  # strikethrough text
        "del",
        "[aria-label*='Regular']",
        "[aria-label*='regular']",
        "span.product-price--original",
    ]

    for sel in sale_selectors:
        el = page.query_selector(sel)
        if el:
            try:
                current_price = _parse_price(el.inner_text())
                break
            except ValueError:
                continue

    for sel in regular_selectors:
        el = page.query_selector(sel)
        if el:
            try:
                original_price = _parse_price(el.inner_text())
                break
            except ValueError:
                continue

    # Strategy 2: Fall back to generic price selectors.
    if current_price is None:
        generic_selectors = [
            "[aria-label='Product Price']",
            "[data-auid='product-price']",
            "[class*='product-price']",
            "[class*='price'] span",
            "[class*='price']",
        ]
        for sel in generic_selectors:
            els = page.query_selector_all(sel)
            prices = []
            for el in els:
                try:
                    prices.append(_parse_price(el.inner_text()))
                except ValueError:
                    continue
            if len(prices) >= 2:
                # Two prices visible → the lower one is the sale price.
                current_price = min(prices)
                original_price = max(prices)
                break
            elif len(prices) == 1:
                current_price = prices[0]
                break

    if current_price is None:
        raise RuntimeError("Could not find any price on the page")

    on_sale = original_price is not None and original_price > current_price

    return current_price, original_price, on_sale
