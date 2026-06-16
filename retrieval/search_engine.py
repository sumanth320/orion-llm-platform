import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
# 1. Import both core classes directly from the consolidated root namespace
from fastembed import TextEmbedding
from sentence_transformers import CrossEncoder

# Load environment configurations safely
load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "financial_articles"

# 2. Instantiate dense retrieval and cross-encoder reranker models
dense_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
rerank_model = CrossEncoder("BAAI/bge-reranker-base")

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def execute_hybrid_reranked_search(query_text: str, metadata_filters: dict = None, candidate_limit: int = 20,
                                   final_top_k: int = 5):
    """
    Executes a two-stage hybrid search pipeline:
    1. Pre-filters payload and performs fast dense vector extraction via Qdrant.
    2. Deeply reranks candidates using a Cross-Encoder model.
    """
    # STAGE 1: Extract candidate pool using vector distance + hard metadata criteria
    query_vector = list(dense_model.embed([query_text]))[0]

    qdrant_filter = None
    if metadata_filters:
        conditions = [
            models.FieldCondition(key=k, match=models.MatchValue(value=v))
            for k, v in metadata_filters.items()
        ]
        qdrant_filter = models.Filter(must=conditions)

    initial_candidates = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=qdrant_filter,
        limit=candidate_limit,  # Pull a broader pool for quality assessment
        with_payload=True
    )

    if not initial_candidates:
        print("No matches discovered matching the filtering criteria.")
        return []

    # STAGE 2: Pass query and results into the Cross-Encoder simultaneously
    documents_to_eval = [res.payload["summary"] for res in initial_candidates]

    # SentenceTransformers CrossEncoder expects (query, document) pairs.
    query_doc_pairs = [(query_text, doc) for doc in documents_to_eval]
    rerank_scores = rerank_model.predict(query_doc_pairs)

    # Map cross-encoder scores back onto the original Qdrant points.
    final_sorted_points = []
    for idx, score in enumerate(rerank_scores):
        original_point = initial_candidates[idx]
        original_point.score = float(score)
        final_sorted_points.append(original_point)

    # Re-sort array based on the fresh neural attention assignments
    final_sorted_points.sort(key=lambda x: x.score, reverse=True)

    return final_sorted_points[:final_top_k]


if __name__ == "__main__":
    # Test execution hook to verify our 248 points are searchable locally
    print("Testing the hybrid retrieval framework...")
    test_query = "Are there any risks or bottlenecks surrounding AI chip supply chains?"

    # Apply a strict ticker limit to verify dynamic filter building
    test_filters = {"ticker": "NVDA"}

    vetted_results = execute_hybrid_reranked_search(
        query_text=test_query,
        metadata_filters=test_filters
    )

    print("\n--- TOP VETTED SEARCH RESULTS ---")
    for rank, point in enumerate(vetted_results, 1):
        print(f"Rank {rank} [Score: {point.score:.4f}]")
        print(f"Headline: {point.payload.get('headline')}")
        print(f"Summary: {point.payload.get('summary')}\n")