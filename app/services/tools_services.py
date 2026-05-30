import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"


def _search_symbol(keywords: str):
    """Resolve symbol dynamically via Finnhub symbol search."""
    if not FINNHUB_API_KEY:
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/search",
            params={"q": keywords, "token": FINNHUB_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return None

    results = data.get("result", [])
    if not results:
        return None

    # Return first common stock match
    for item in results:
        if item.get("type") == "Common Stock":
            return item.get("symbol", "").upper()

    # Fallback to first result
    return results[0].get("symbol", "").upper() or None


def extract_ticker(query: str):
    # 1) Explicit forms: "ticker TSLA", "symbol: nvda"
    explicit = re.search(
        r"(?:ticker|symbol)\s*(?:is|=|:)?\s*\$?([A-Za-z]{1,6}(?:\.[A-Za-z]{1,2})?)",
        query,
        flags=re.IGNORECASE,
    )
    if explicit:
        return explicit.group(1).upper()

    # 2) Dollar-prefixed form: "$aapl"
    dollar = re.search(r"\$([A-Za-z]{1,6}(?:\.[A-Za-z]{1,2})?)", query)
    if dollar:
        return dollar.group(1).upper()

    # 3) Already uppercase ticker in text
    upper_token = re.search(r"\b([A-Z]{1,6}(?:\.[A-Z]{1,2})?)\b", query)
    if upper_token:
        return upper_token.group(1).upper()

    # 4) Dynamic fallback for lowercase tickers or company names
    return _search_symbol(query)


def get_stock_price(ticker: str):
    try:
        response = requests.get(
            f"{BASE_URL}/quote",
            params={"symbol": ticker, "token": FINNHUB_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        quote = response.json()
    except requests.RequestException:
        return {
            "tool": "stock_price",
            "ticker": ticker,
            "price": 0,
            "change": 0,
            "change_percent": "0%",
            "raw_timestamp": None
        }

    current_price = quote.get("c", 0)   # current price
    prev_close    = quote.get("pc", 0)  # previous close
    change        = quote.get("d", 0)   # change
    change_pct    = quote.get("dp", 0)  # change percent

    return {
        "tool": "stock_price",
        "ticker": ticker,
        "price": float(current_price or 0),
        "change": float(change or 0),
        "change_percent": f"{float(change_pct or 0):.2f}%",
        "raw_timestamp": prev_close   # Finnhub doesn't return trading day, use prev close instead
    }
