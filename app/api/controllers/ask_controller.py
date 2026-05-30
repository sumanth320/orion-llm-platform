from app.observability.trace_logger import Logger
from app.orchestration.orchestrator import route_query
from app.orchestration.prompt_builder import build_prompt
from app.services.llm.ollama_client import generate_response


def handle_ask(question: str, user_id: str, session_id: str):
    logger = Logger()
    logger.start()

    logger.log("query", question)
    logger.log("user_id", user_id)
    logger.log("session_id", session_id)

    routed = route_query(question)
    logger.log("route_decision", routed["route"])

    if "debug" in routed:
        logger.log("routing_debug", routed["debug"])

    if routed["route"] == "clarify":
        logger.log("final_status", "clarify")
        logger.end()
        logger.print()

        return {
            "message": routed["message"],
            "debug": routed.get("debug"),
        }

    messages = build_prompt(
        query=routed["query"],
        route=routed["route"],
        context=routed["context"],
    )

    answer = generate_response(messages)

    logger.log("final_status", "success")
    logger.end()
    logger.print()

    return {
        "route": routed["route"],
        "answer": answer,
        "debug": routed.get("debug"),
    }
