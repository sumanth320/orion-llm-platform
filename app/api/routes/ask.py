from fastapi import APIRouter

from app.api.handlers.ask_handler import handle_ask
from app.api.schemas.ask import AskRequest

router = APIRouter()


@router.post("/ask")
def ask(request: AskRequest):
    return handle_ask(
        question=request.question,
        user_id=request.user_id,
        session_id=request.session_id,
    )
