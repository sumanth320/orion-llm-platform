from typing import Any, Dict, Optional, TypedDict


class RoutedQuery(TypedDict, total=False):
    route: str
    query: str
    context: Optional[Any]
    message: str
    debug: Dict[str, Any]

