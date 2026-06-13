import os
import sys
import uuid
from datetime import datetime, timedelta
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

# 1. Initialize System Configurations
load_dotenv()

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_KEY:
    print("Error: FINNHUB_API_KEY variable not found in environment configurations.", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://finnhub.io/api/v1"
COLLECTION_NAME = "financial_articles"
BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "8"))
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
FASTEMBED_MODEL_NAME = os.getenv("FASTEMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
FASTEMBED_CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", "/app/.cache/fastembed")

_qdrant_client = None
_embedding_model = None


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _qdrant_client


def get_embedding_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        # Load the local embedding model only when it is actually needed.
        _embedding_model = TextEmbedding(
            model_name=FASTEMBED_MODEL_NAME,
            cache_dir=FASTEMBED_CACHE_DIR,
            threads=1,
        )
    return _embedding_model


# 2. Data Models
class FinancialDocument(BaseModel):
    ticker: str
    headline: str
    summary: str
    source: str
    url: str
    published_at: datetime
    company_industry: str = Field(default="Unknown")


# 3. Ingestion Tasks
def initialize_vector_store():
    """Initializes the Qdrant database collection schema using production dimensions safely."""
    print(f"Checking vector database for collection: '{COLLECTION_NAME}'...")
    try:
        qdrant_client = get_qdrant_client()

        # Protect existing records if the schema is already established
        if qdrant_client.collection_exists(collection_name=COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' is active and ready. Preserving existing points.")
            return

        print(f"Initializing production collection: '{COLLECTION_NAME}' (384 Dimensions)...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
        print(f"Successfully instantiated production collection: '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"Database Connection Error: Could not talk to Qdrant container: {e}")

def fetch_company_metadata(ticker: str) -> dict:
    url = f"{BASE_URL}/stock/profile2"
    params = {"symbol": ticker, "token": FINNHUB_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to retrieve profile metadata for {ticker}: {e}")
        return {}


def fetch_company_news(ticker: str, days_back: int = 5) -> list[FinancialDocument]:
    print(f"Initiating financial news ingestion pipeline for symbol: {ticker}")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    meta = fetch_company_metadata(ticker)
    industry = meta.get("finnhubIndustry", "Unknown")

    url = f"{BASE_URL}/company-news"
    params = {
        "symbol": ticker,
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "token": FINNHUB_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw_articles = response.json()

        processed_documents = []
        for art in raw_articles:
            if not art.get("headline") or not art.get("summary"):
                continue

            doc = FinancialDocument(
                ticker=ticker,
                headline=art["headline"],
                summary=art["summary"],
                source=art.get("source", "Unknown"),
                url=art.get("url", ""),
                published_at=datetime.fromtimestamp(art["datetime"]),
                company_industry=industry
            )
            processed_documents.append(doc)

        print(f"Successfully processed {len(processed_documents)} valid data payloads from Finnhub.")
        return processed_documents
    except requests.exceptions.RequestException as e:
        print(f"Pipeline Execution Failure: Network connection dropped during fetch: {e}", file=sys.stderr)
        return []


def push_documents_to_vector_store(documents: list[FinancialDocument]):
    """Converts text structures to vectors and performs a batch upsert into Qdrant."""
    if not documents:
        print("No documents found to process.")
        return

    qdrant_client = get_qdrant_client()
    embedding_model = get_embedding_model()

    print(f"Preparing to vectorize and upsert {len(documents)} documents in batches of {BATCH_SIZE}...")

    for start_idx in range(0, len(documents), BATCH_SIZE):
        batch_docs = documents[start_idx:start_idx + BATCH_SIZE]
        batch_texts = [f"Headline: {doc.headline}. Summary: {doc.summary}" for doc in batch_docs]

        print(f"Generating embeddings for batch {start_idx // BATCH_SIZE + 1}...")
        vectors_list = list(embedding_model.embed(batch_texts))

        qdrant_points = []
        for idx, doc in enumerate(batch_docs):
            qdrant_points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vectors_list[idx].tolist(),
                    payload={
                        "ticker": doc.ticker,
                        "headline": doc.headline,
                        "summary": doc.summary,
                        "source": doc.source,
                        "url": doc.url,
                        "published_at": doc.published_at.isoformat(),
                        "company_industry": doc.company_industry,
                    },
                )
            )

        print(f"Upserting batch {start_idx // BATCH_SIZE + 1} into collection '{COLLECTION_NAME}'...")
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=qdrant_points)

    print("Database sync complete. Points stored successfully.")


if __name__ == "__main__":
    # Ensure our vector schema is active and correct
    initialize_vector_store()

    # Ingest historical text logs from Finnhub API
    target_ticker = "NVDA"
    documents_payload = fetch_company_news(target_ticker, days_back=3)

    # Vectorize and push to permanent storage
    if documents_payload:
        push_documents_to_vector_store(documents_payload)