#!/usr/bin/env python3
"""End-to-end live test using a local HTTP server to simulate Aritzia pages.

Spins up a real HTTP server, points the scraper at it, and verifies the full
pipeline: scrape → store → detect price drop → (skip email, no creds).
"""

import http.server
import json
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import scrape_product
from storage import update_price, get_last_price

# ── HTML templates ────────────────────────────────────────────

PRODUCT_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head><title>{name} | Aritzia US</title></head>
<body>
  <div class="product-detail">
    <h1 class="product-name">{name}</h1>
    <div class="product-price" aria-label="Product Price">
      {price_html}
    </div>
  </div>
</body>
</html>
"""


def _make_regular_page(name: str, price: float) -> str:
    return PRODUCT_PAGE_TEMPLATE.format(
        name=name,
        price_html=f'<span class="price">${price:.2f}</span>',
    )


def _make_sale_page(name: str, original: float, sale: float) -> str:
    return PRODUCT_PAGE_TEMPLATE.format(
        name=name,
        price_html=(
            f'<s class="regular-price">${original:.2f}</s>\n'
            f'      <span class="sale-price">${sale:.2f}</span>'
        ),
    )


# ── Local HTTP server ─────────────────────────────────────────

class _Handler(http.server.BaseHTTPRequestHandler):
    """Serves whatever HTML is set on the class-level `pages` dict."""

    pages: dict[str, str] = {}

    def do_GET(self):
        page = self.pages.get(self.path)
        if page is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode())

    def log_message(self, format, *args):
        pass  # suppress request logs


def _start_server() -> tuple[http.server.HTTPServer, int]:
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


# ── Tests ─────────────────────────────────────────────────────

def test_full_pipeline():
    """Simulate two price checks: first at full price, then a sale."""
    server, port = _start_server()
    tmp_json = Path(tempfile.mktemp(suffix=".json"))
    product_name = "The Effortless Pant™"
    url = f"http://127.0.0.1:{port}/product/effortless-pant"

    try:
        # ── Check 1: Full price ───────────────────────────────
        _Handler.pages["/product/effortless-pant"] = _make_regular_page(
            product_name, 148.00
        )

        print(f"[Check 1] Scraping full-price product at {url} ...")
        product = scrape_product(url, timeout_ms=10000)

        assert product.name == product_name, f"Expected '{product_name}', got '{product.name}'"
        assert product.current_price == 148.00, f"Expected 148.00, got {product.current_price}"
        assert product.on_sale is False
        print(f"  -> Name: {product.name}")
        print(f"  -> Price: ${product.current_price:.2f}")
        print(f"  -> On sale: {product.on_sale}")

        prev = update_price(url, product.name, product.current_price, path=tmp_json)
        assert prev is None, "First check should have no previous price"
        print("  -> Stored in price history (first entry)")
        print("  PASS: Full-price scrape + storage\n")

        # ── Check 2: Price drop (sale) ────────────────────────
        _Handler.pages["/product/effortless-pant"] = _make_sale_page(
            product_name, 148.00, 98.00
        )

        print(f"[Check 2] Scraping sale-price product at {url} ...")
        product = scrape_product(url, timeout_ms=10000)

        assert product.current_price == 98.00, f"Expected 98.00, got {product.current_price}"
        assert product.original_price == 148.00
        assert product.on_sale is True
        print(f"  -> Price: ${product.current_price:.2f} (was ${product.original_price:.2f})")
        print(f"  -> On sale: {product.on_sale}")

        prev = update_price(url, product.name, product.current_price, path=tmp_json)
        assert prev == 148.00, f"Expected previous price 148.00, got {prev}"

        drop = prev - product.current_price
        pct = (drop / prev) * 100
        print(f"  -> Price drop detected: ${prev:.2f} -> ${product.current_price:.2f} (-${drop:.2f}, {pct:.1f}% off)")
        print("  -> Email alert would fire here (skipped — no credentials)")
        print("  PASS: Sale detection + price drop\n")

        # ── Verify stored history ─────────────────────────────
        data = json.loads(tmp_json.read_text())
        entry = data[url]
        assert len(entry["history"]) == 2
        assert entry["last_price"] == 98.00
        print(f"[History] {len(entry['history'])} price checks recorded")
        print(f"  -> Last price: ${entry['last_price']:.2f}")
        print(f"  -> Timestamps: {[h['timestamp'] for h in entry['history']]}")
        print("  PASS: Price history integrity\n")

        # ── Check 3: No change ────────────────────────────────
        print(f"[Check 3] Re-checking same sale price ...")
        product = scrape_product(url, timeout_ms=10000)
        prev = update_price(url, product.name, product.current_price, path=tmp_json)
        assert prev == 98.00
        print(f"  -> Still ${product.current_price:.2f} — no change, no alert")
        print("  PASS: No false alert on stable price\n")

        print("=" * 50)
        print("ALL LIVE TESTS PASSED")
        print("=" * 50)

    finally:
        tmp_json.unlink(missing_ok=True)
        server.shutdown()


if __name__ == "__main__":
    test_full_pipeline()
