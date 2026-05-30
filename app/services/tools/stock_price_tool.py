from app.services.tools.finnhub_client import quote_symbol


def get_stock_price(ticker: str):
    quote = quote_symbol(ticker)
    if quote is None:
        return {
            "tool": "stock_price",
            "ticker": ticker,
            "price": 0,
            "change": 0,
            "change_percent": "0%",
            "raw_timestamp": None,
        }

    current_price = quote.get("c", 0)
    prev_close = quote.get("pc", 0)
    change = quote.get("d", 0)
    change_pct = quote.get("dp", 0)

    return {
        "tool": "stock_price",
        "ticker": ticker,
        "price": float(current_price or 0),
        "change": float(change or 0),
        "change_percent": f"{float(change_pct or 0):.2f}%",
        "raw_timestamp": prev_close,
    }

