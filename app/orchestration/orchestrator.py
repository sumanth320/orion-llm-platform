from app.orchestration.decision_engine import choose_route
from app.orchestration.handlers.rag_handler import handle_rag_route
from app.orchestration.handlers.tool_handler import handle_tool_route
from app.orchestration.state import RoutedQuery


def route_query(query: str) -> RoutedQuery:
    best_route, best_score, debug = choose_route(query)

    if best_route == "tool":
        return handle_tool_route(query=query, best_score=best_score, debug=debug)

    if best_route == "direct":
        debug["entered_branch"] = "direct"
        debug["decision"] = "direct_by_intent"
        return {
            "route": "direct",
            "query": query,
            "context": None,
            "debug": debug,
        }

    return handle_rag_route(query=query, debug=debug)
