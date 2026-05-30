import os

import requests
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"


def search_symbol(keywords: str):
    if not FINNHUB_API_KEY:
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/search",
            params={"q": keywords, "token": FINNHUB_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return None

    results = data.get("result", [])
    if not results:
        return None

    for item in results:
        if item.get("type") == "Common Stock":
            return item.get("symbol", "").upper()

    return results[0].get("symbol", "").upper() or None


def quote_symbol(ticker: str):
    try:
        response = requests.get(
            f"{BASE_URL}/quote",
            params={"symbol": ticker, "token": FINNHUB_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

