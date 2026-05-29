from app.prefilter import compute_intent_scores
from app.rag import retrieve
from app.tools import get_stock_price, extract_ticker
from app.config import RAG_CONFIG, HIGH_CONFIDENCE


def get_dynamic_k(top1, top2):
    gap = top1 - top2 if top2 is not None else 1.0
    if gap >= RAG_CONFIG["high_gap"]:
        return RAG_CONFIG["k_small"]
    if gap >= RAG_CONFIG["low_gap"]:
        return RAG_CONFIG["k_medium"]
    return RAG_CONFIG["k_large"]


def is_rag_reliable(top1_score):
    return top1_score >= RAG_CONFIG["min_top1_score"]


def route_query(query: str):
    scores = compute_intent_scores(query)
    best_route = max(scores, key=scores.get)
    best_score = scores[best_route]

    debug = {
        "query": query,
        "intent_scores": {k: float(v) for k, v in scores.items()},
        "best_route": best_route,
        "best_score": float(best_score),
        "high_confidence_threshold": float(HIGH_CONFIDENCE),
    }

    if best_route == "tool":
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

    if best_route == "direct":
        debug["entered_branch"] = "direct"
        debug["decision"] = "direct_by_intent"
        return {
            "route": "direct",
            "query": query,
            "context": None,
            "debug": debug,
        }

    debug["entered_branch"] = "rag_candidate"
    chunks = retrieve(query)
    debug["retrieved_chunk_count"] = len(chunks)

    if not chunks:
        debug["decision"] = "direct_no_rag_chunks"
        return {
            "route": "direct",
            "query": query,
            "context": None,
            "debug": debug,
        }

    top1 = chunks[0]["score"]
    top2 = chunks[1]["score"] if len(chunks) > 1 else None
    debug["rag_top1"] = float(top1)
    debug["rag_top2"] = float(top2) if top2 is not None else None

    if not is_rag_reliable(top1):
        debug["decision"] = "direct_low_rag_confidence"
        return {
            "route": "direct",
            "query": query,
            "context": None,
            "debug": debug,
        }

    k = get_dynamic_k(top1, top2)

    for chunk in chunks[:k]:
        print(chunk["chunk"])
        print("=" * 50)

    debug["rag_dynamic_k"] = int(k)
    debug["decision"] = "rag"

    return {
        "route": "rag",
        "query": query,
        "context": chunks[:k],
        "debug": debug,
    }
