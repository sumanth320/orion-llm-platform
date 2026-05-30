import re

from app.services.tools.finnhub_client import search_symbol


def extract_ticker(query: str):
    explicit = re.search(
        r"(?:ticker|symbol)\s*(?:is|=|:)?\s*\$?([A-Za-z]{1,6}(?:\.[A-Za-z]{1,2})?)",
        query,
        flags=re.IGNORECASE,
    )
    if explicit:
        return explicit.group(1).upper()

    dollar = re.search(r"\$([A-Za-z]{1,6}(?:\.[A-Za-z]{1,2})?)", query)
    if dollar:
        return dollar.group(1).upper()

    upper_token = re.search(r"\b([A-Z]{1,6}(?:\.[A-Z]{1,2})?)\b", query)
    if upper_token:
        return upper_token.group(1).upper()

    return search_symbol(query)

