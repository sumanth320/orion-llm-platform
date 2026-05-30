from app.observability.trace_logger import Logger
from app.orchestration.orchestrator import run
from app.orchestration.prompt_builder import build_prompt
from app.services.llm.ollama_client import generate_response


def handle_ask(question: str, user_id: str, session_id: str):

    logger = Logger()
    logger.start()

    logger.log("query", question)
    logger.log("user_id", user_id)
    logger.log("session_id", session_id)

    result = run(question)

    logger.log("route_decision", result["route"])

    if "debug" in result:
        logger.log("routing_debug", result["debug"])

    if result["route"] == "clarify":

        logger.log("final_status", "clarify")

        logger.end()
        logger.print()

        return result

    messages = build_prompt(
        query=result["query"],
        route=result["route"],
        context=result["context"],
    )

    answer = generate_response(messages)

    logger.log("final_status", "success")

    logger.end()
    logger.print()

    return {
        "route": result["route"],
        "answer": answer,
        "debug": result.get("debug"),
    }