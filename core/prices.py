import difflib
import json
import os
import sys
import time
import sys
import urllib.request

from core.config import get as get_config

CACHE_PATH = os.path.expanduser("~/.FinTrack/prices_cache.json")
CACHE_TTL = 30 * 60  # seconds, matches UEX's own cache


def _bundled_token():
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(base, "uex_key.txt")) as f:
            return f.read().strip()
    except OSError:
        return ""


def fetch_raw():
    base = get_config("uex_api_base").rstrip("/")
    req = urllib.request.Request(
        f"{base}/commodities_prices_all",
        headers={"Accept": "application/json", "User-Agent": "FinTrack"},
    )
    token = get_config("uex_api_token") or _bundled_token()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.load(resp)
    if payload.get("status") != "ok":
        raise RuntimeError(f"UEX returned status: {payload.get('status')}")
    return payload["data"]


def fetch_prices():
    return _aggregate(fetch_raw())


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
    return {
        name: {
            "buy": int(sum(e["buy"]) / len(e["buy"])) if e["buy"] else 0,
            "sell": int(sum(e["sell"]) / len(e["sell"])) if e["sell"] else 0,
        }
        for name, e in acc.items()
    }


def _build(rows):
    """Averages plus the per-terminal list (same _avg fields as the averages)."""
    terminals = {}
    for r in rows:
        name = r.get("commodity_name")
        if not name:
            continue
        terminals.setdefault(name, []).append({
            "terminal": r.get("terminal_name") or "Unknown",
            "buy": int(r.get("price_buy_avg") or 0),
            "sell": int(r.get("price_sell_avg") or 0),
        })
    return {"prices": _aggregate(rows), "terminals": terminals}


def fetch_prices():
    return _aggregate(fetch_raw())


def get_data():
    """Cached lookup that never raises. Empty data if nothing is available."""
    cached = None
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                cached = json.load(f)
            if "data" not in cached:  # old cache format
                cached = None
        except Exception:
            cached = None

    if cached and time.time() - cached.get("fetched", 0) < CACHE_TTL:
        return cached["data"]

    try:
        data = _build(fetch_raw())
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w") as f:
            json.dump({"fetched": time.time(), "data": data}, f)
        return data
    except Exception:
        # API down or blocked: fall back to stale cache if we have one
        return cached["data"] if cached else {"prices": {}, "terminals": {}}


def get_prices():
    return get_data()["prices"]


def list_commodities():
    return sorted(get_prices().keys())


def get_price(commodity, side="sell"):
    """side: 'sell' = what you receive selling, 'buy' = what you pay buying."""
    return get_prices().get(commodity, {}).get(side, 0)


def best_terminals(commodity, side="sell", limit=5):
    """Best places to sell (highest price) or buy (lowest price)."""
    rows = [r for r in get_data()["terminals"].get(commodity, []) if r[side] > 0]
    rows.sort(key=lambda r: r[side], reverse=(side == "sell"))
    return rows[:limit]


def find_commodity(query):
    """Resolve typed text to a real commodity name, or None."""
    lower = {n.lower(): n for n in get_prices()}
    q = query.lower()
    if q in lower:
        return lower[q]
    starts = [n for l, n in lower.items() if l.startswith(q)]
    if len(starts) == 1:
        return starts[0]
    close = difflib.get_close_matches(q, list(lower), n=1, cutoff=0.6)
    return lower[close[0]] if close else None
