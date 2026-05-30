from app.core.config import HIGH_CONFIDENCE, RAG_CONFIG
from app.orchestration.prefilter import compute_intent_scores
from app.orchestration.state import State


def get_dynamic_k(top1, top2):
    gap = top1 - top2 if top2 is not None else 1.0
    if gap >= RAG_CONFIG["high_gap"]:
        return RAG_CONFIG["k_small"]
    if gap >= RAG_CONFIG["low_gap"]:
        return RAG_CONFIG["k_medium"]
    return RAG_CONFIG["k_large"]


def is_rag_reliable(top1_score):
    return top1_score >= RAG_CONFIG["min_top1_score"]


def choose_state(query: str):

    scores = compute_intent_scores(query)

    best_route = max(scores, key=scores.get)
    best_score = float(scores[best_route])

    debug = {
        "query": query,
        "intent_scores": {k: float(v) for k, v in scores.items()},
        "best_route": best_route,
        "best_score": best_score,
        "high_confidence_threshold": float(HIGH_CONFIDENCE),
    }

    state_mapping = {
        "direct": State.DIRECT,
        "rag": State.RAG,
        "tool": State.TOOL,
    }

    return state_mapping[best_route], best_score, debug
