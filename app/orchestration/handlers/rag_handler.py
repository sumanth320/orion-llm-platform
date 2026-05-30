from app.orchestration.decision_engine import get_dynamic_k, is_rag_reliable
from app.retrieval.rag import retrieve


def handle_rag_route(query: str, debug: dict):
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
    debug["rag_dynamic_k"] = int(k)
    debug["decision"] = "rag"

    return {
        "route": "rag",
        "query": query,
        "context": chunks[:k],
        "debug": debug,
    }

