import json
import os
import time
import urllib.request

from core.config import get as get_config

CACHE_PATH = os.path.expanduser("~/.FinTrack/prices_cache.json")
CACHE_TTL = 30 * 60  # seconds, matches UEX's own cache


def fetch_prices():
    """Hit the API and return {commodity: {"buy": int, "sell": int}}.
    Raises on any failure so callers/tests can see the real error."""
    base = get_config("uex_api_base").rstrip("/")
    req = urllib.request.Request(
        f"{base}/commodities_prices_all",
        headers={"Accept": "application/json", "User-Agent": "FinTrack"},
    )
    token = get_config("uex_api_token")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.load(resp)

    if payload.get("status") != "ok":
        raise RuntimeError(f"UEX returned status: {payload.get('status')}")
    return _aggregate(payload["data"])


def _aggregate(rows):
    """Average each commodity's price across all terminals that report one."""
    acc = {}
    for r in rows:
        name = r.get("commodity_name")
        if not name:
            continue
        entry = acc.setdefault(name, {"buy": [], "sell": []})
        if (r.get("price_buy_avg") or 0) > 0:
            entry["buy"].append(r["price_buy_avg"])
        if (r.get("price_sell_avg") or 0) > 0:
            entry["sell"].append(r["price_sell_avg"])

    result = {}
    for name, e in acc.items():
        result[name] = {
            "buy": int(sum(e["buy"]) / len(e["buy"])) if e["buy"] else 0,
            "sell": int(sum(e["sell"]) / len(e["sell"])) if e["sell"] else 0,
        }
    return result


def get_prices():
    """Cached lookup that never raises. Returns {} if nothing is available."""
    cached = None
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                cached = json.load(f)
        except Exception:
            cached = None

    if cached and time.time() - cached.get("fetched", 0) < CACHE_TTL:
        return cached["prices"]

    try:
        prices = fetch_prices()
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w") as f:
            json.dump({"fetched": time.time(), "prices": prices}, f)
        return prices
    except Exception:
        # API down or blocked: fall back to stale cache if we have one
        return cached["prices"] if cached else {}


def list_commodities():
    return sorted(get_prices().keys())


def get_price(commodity, side="sell"):
    """side: 'sell' = what you receive selling, 'buy' = what you pay buying."""
    return get_prices().get(commodity, {}).get(side, 0)