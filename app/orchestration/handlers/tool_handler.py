from app.core.config import HIGH_CONFIDENCE
from app.services.tools.stock_price_tool import get_stock_price
from app.services.tools.ticker_extractor import extract_ticker


def handle_tool_route(query: str, best_score: float, debug: dict):
    debug["entered_branch"] = "tool"

    if best_score < HIGH_CONFIDENCE:
        debug["decision"] = "clarify_low_tool_confidence"
        return {
            "route": "clarify",
            "message": "Could you specify the stock symbol or company name?",
            "debug": debug,
        }

    ticker = extract_ticker(query)
    debug["extracted_ticker"] = ticker

    if not ticker:
        debug["decision"] = "clarify_ticker_not_found"
        return {
            "route": "clarify",
            "message": "Could you specify the stock symbol (e.g. AAPL)?",
            "debug": debug,
        }

    tool_result = get_stock_price(ticker)
    debug["tool_result_preview"] = {
        "ticker": tool_result.get("ticker"),
        "price": tool_result.get("price"),
        "change_percent": tool_result.get("change_percent"),
    }
    debug["decision"] = "tool"

    return {
        "route": "tool",
        "query": query,
        "context": tool_result,
        "debug": debug,
    }

