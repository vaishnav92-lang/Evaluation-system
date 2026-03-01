"""Read/write price history to a local JSON file."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).parent / "price_history.json"


def _load(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, indent=2))


def get_last_price(url: str, path: Path = DEFAULT_PATH) -> float | None:
    """Return the last known price for a product URL, or None if unseen."""
    data = _load(path)
    entry = data.get(url)
    if entry is None:
        return None
    return entry.get("last_price")


def update_price(
    url: str,
    name: str,
    price: float,
    path: Path = DEFAULT_PATH,
) -> float | None:
    """Record a new price check. Returns the previous price (or None if first check).

    The JSON structure per URL:
    {
      "url": "...",
      "name": "...",
      "last_price": 98.0,
      "last_checked": "2026-03-01T12:00:00+00:00",
      "history": [
        {"price": 98.0, "timestamp": "2026-03-01T12:00:00+00:00"},
        ...
      ]
    }
    """
    data = _load(path)
    now = datetime.now(timezone.utc).isoformat()

    previous_price = None
    if url in data:
        previous_price = data[url].get("last_price")

    entry = data.get(url, {"url": url, "name": name, "history": []})
    entry["name"] = name
    entry["last_price"] = price
    entry["last_checked"] = now
    entry["history"].append({"price": price, "timestamp": now})

    data[url] = entry
    _save(data, path)

    logger.info("Stored price $%.2f for %s", price, name)
    return previous_price
