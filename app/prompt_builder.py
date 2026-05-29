def build_prompt(query: str, route: str, context=None):
    if route == "rag":
        joined = "\n\n".join([c["chunk"] for c in context])

        return [
            {
                "role": "system",
                "content": "Use only the supplied context."
            },
            {
                "role": "user",
                "content": f"Context:\n{joined}\n\nQuestion:\n{query}"
            }
        ]

    if route == "tool":
        tool_context = f"""
Stock symbol: {context['ticker']}
Current price: {context['price']} USD
Daily change: {context['change']}
Change percent: {context['change_percent']}
Trading day: {context['raw_timestamp']}
"""

        return [
            {
                "role": "system",
                "content": "You are a financial assistant. Use only supplied market data."
            },
            {
                "role": "user",
                "content": f"{tool_context}\n\nQuestion:\n{query}"
            }
        ]

    return [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": query
        }
    ]