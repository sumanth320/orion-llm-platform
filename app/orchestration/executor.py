from app.orchestration.state import State, ExecutionContext

from app.orchestration.handlers.rag_handler import handle_rag_route
from app.orchestration.handlers.tool_handler import handle_tool_route


def execute(ctx: ExecutionContext):

    if ctx.state == State.TOOL:
        return handle_tool_route(
            query=ctx.query,
            best_score=float(ctx.best_score or 0.0),
            debug=ctx.debug,
        )

    if ctx.state == State.RAG:
        return handle_rag_route(
            query=ctx.query,
            debug=ctx.debug,
        )

    if ctx.state == State.DIRECT:

        ctx.debug["entered_branch"] = "direct"
        ctx.debug["decision"] = "direct_by_intent"

        return {
            "route": "direct",
            "query": ctx.query,
            "context": None,
            "debug": ctx.debug,
        }

    raise ValueError(f"Unknown state: {ctx.state}")