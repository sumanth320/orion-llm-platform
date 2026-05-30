from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    user_id: str
    session_id: str

