from core.prices import fetch_prices

try:
    prices = fetch_prices()
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
else:
    print(f"OK, {len(prices)} commodities")
    for name in list(prices)[:8]:
        print(f"  {name}: buy {prices[name]['buy']:,} / sell {prices[name]['sell']:,} per SCU")