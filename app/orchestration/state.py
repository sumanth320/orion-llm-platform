from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional


class State(str, Enum):
    DIRECT = "direct"
    RAG = "rag"
    TOOL = "tool"
    CLARIFY = "clarify"


@dataclass
class ExecutionContext:
    query: str
    state: Optional[State] = None
    best_score: Optional[float] = None
    context: Optional[Any] = None
    message: Optional[str] = None
    debug: Optional[Dict[str, Any]] = None