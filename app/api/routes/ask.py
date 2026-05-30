from fastapi import APIRouter
from pydantic import BaseModel

from app.orchestration.orchestrator import route_query
from app.utils.prompt_builder import build_prompt
from app.services.llm_service import generate_response
from app.core.logger import Logger

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    user_id: str
    session_id: str


@router.post("/ask")
def ask(request: AskRequest):
    logger = Logger()
    logger.start()

    logger.log("query", request.question)
    logger.log("user_id", request.user_id)
    logger.log("session_id", request.session_id)

    routed = route_query(request.question)
    logger.log("route_decision", routed["route"])

    if "debug" in routed:
        logger.log("routing_debug", routed["debug"])

    if routed["route"] == "clarify":
        logger.log("final_status", "clarify")
        trace = logger.end()
        logger.print()

        return {
            "message": routed["message"],
            "debug": routed.get("debug")
        }

    messages = build_prompt(
        query=routed["query"],
        route=routed["route"],
        context=routed["context"]
    )

    answer = generate_response(messages)

    logger.log("final_status", "success")
    trace = logger.end()
    logger.print()

    return {
        "route": routed["route"],
        "answer": answer,
        "debug": routed.get("debug")
    }