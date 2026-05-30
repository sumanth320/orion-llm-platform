from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

ROUTES = {
    "rag": [
        "margin trading explanation",
        "what is options trading",
        "what is moving average",
        "how to read candlestick charts",
        "RSI indicator interpretation",
        "support and resistance levels"
    ],
    "tool": [
        "stock price",
        "share price",
        "ticker quote",
        "market price",
        "current price of",
        "get quote for"
    ],
    "direct": [
        "investment recommendation",
        "should I buy this stock",
        "compare stocks performance",
        "which sector is best now"
    ]
}

route_embeddings = {
    route: model.encode(examples)
    for route, examples in ROUTES.items()
}


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def compute_intent_scores(query: str):
    query_emb = model.encode(query)

    scores = {}

    for route, embeddings in route_embeddings.items():
        sims = [cosine(query_emb, e) for e in embeddings]
        scores[route] = max(sims)

    return scores