"""Tests for the scraper and storage modules using local HTML fixtures."""

import json
import sys
import tempfile
from pathlib import Path

# Ensure the parent package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import scrape_product
from storage import update_price, get_last_price

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _file_url(name: str) -> str:
    return f"file://{FIXTURES / name}"


# ── Scraper tests ──────────────────────────────────────────────


def test_non_sale_product():
    result = scrape_product(_file_url("product_no_sale.html"), timeout_ms=5000)
    assert result.name == "The Effortless Pant™"
    assert result.current_price == 148.00
    assert result.original_price is None
    assert result.on_sale is False
    print("PASS: test_non_sale_product")


def test_sale_product():
    result = scrape_product(_file_url("product_on_sale.html"), timeout_ms=5000)
    assert result.name == "The Effortless Pant™"
    assert result.current_price == 98.00
    assert result.original_price == 148.00
    assert result.on_sale is True
    print("PASS: test_sale_product")


def test_no_price_raises():
    try:
        scrape_product(_file_url("product_no_price.html"), timeout_ms=5000)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "Could not find any price" in str(e)
    print("PASS: test_no_price_raises")


def test_missing_file_raises():
    try:
        scrape_product("file:///tmp/nonexistent_page.html", timeout_ms=5000)
        assert False, "Should have raised RuntimeError"
    except RuntimeError:
        pass
    print("PASS: test_missing_file_raises")


# ── Storage tests ──────────────────────────────────────────────


def test_storage_lifecycle():
    tmp = Path(tempfile.mktemp(suffix=".json"))
    url = "https://example.com/product/1"

    try:
        # First lookup — no history.
        assert get_last_price(url, path=tmp) is None

        # First record.
        prev = update_price(url, "Test Product", 148.00, path=tmp)
        assert prev is None

        # Same price.
        prev = update_price(url, "Test Product", 148.00, path=tmp)
        assert prev == 148.00

        # Price drop.
        prev = update_price(url, "Test Product", 98.00, path=tmp)
        assert prev == 148.00

        # Verify JSON structure.
        data = json.loads(tmp.read_text())
        entry = data[url]
        assert len(entry["history"]) == 3
        assert entry["last_price"] == 98.00

        print("PASS: test_storage_lifecycle")
    finally:
        tmp.unlink(missing_ok=True)


# ── Run all ────────────────────────────────────────────────────

if __name__ == "__main__":
    test_non_sale_product()
    test_sale_product()
    test_no_price_raises()
    test_missing_file_raises()
    test_storage_lifecycle()
    print("\nAll tests passed.")
