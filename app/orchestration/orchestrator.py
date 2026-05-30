from app.orchestration.state import ExecutionContext
from app.orchestration.decision_engine import choose_state
from app.orchestration.executor import execute


def run(query: str):

    state, best_score, debug = choose_state(query)

    ctx = ExecutionContext(
        query=query,
        state=state,
        best_score=best_score,
        debug=debug,
    )

    return execute(ctx)