import os
import sys
from datetime import datetime, timedelta
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 1. Initialize and Validate Local Environment Configuration
# Load the .env file from the root directory path
load_dotenv()

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_KEY:
    print("Error: FINNHUB_API_KEY variable not found in environment configurations.", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://finnhub.io/api/v1"


# 2. Define Data Structures using Pydantic
# This guarantees structural integrity and data validation before data storage
class FinancialDocument(BaseModel):
    ticker: str
    headline: str
    summary: str
    source: str
    url: str
    published_at: datetime
    company_industry: str = Field(default="Unknown")


def fetch_company_metadata(ticker: str) -> dict:
    """Fetches high-level metadata fields used for subsequent vector database filtering."""
    url = f"{BASE_URL}/stock/profile2"
    params = {"symbol": ticker, "token": FINNHUB_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to retrieve profile metadata for {ticker}: {e}")
        return {}


def fetch_company_news(ticker: str, days_back: int = 7) -> list[FinancialDocument]:
    """Ingests raw unstructured text articles from the financial API layer."""
    print(f"Initiating financial news ingestion pipeline for symbol: {ticker}")

    # Calculate dates required by Finnhub format (YYYY-MM-DD)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Fetch background corporate profile metadata for hybrid structure tracking
    meta = fetch_company_metadata(ticker)
    industry = meta.get("finnhubIndustry", "Unknown")

    # Configure API payload requests parameters
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
            # Drop entries missing text fields necessary for vector chunk generation
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

        print(f"Successfully processed {len(processed_documents)} valid data payloads for {ticker}.")
        return processed_documents

    except requests.exceptions.RequestException as e:
        print(f"Pipeline Execution Failure: Network connection dropped during fetch: {e}", file=sys.stderr)
        return []


if __name__ == "__main__":
    # Test execution trace directly via local runtime engine using a primary tech ticker
    target_ticker = "NVDA"
    documents = fetch_company_news(target_ticker, days_back=5)

    if documents:
        print(f"\n--- INGESTION VERIFICATION TRACE (Total Document Records: {len(documents)}) ---")
        # Output a verification breakdown sample from the top record
        sample = documents[0]
        print(f"Target Industry Group: {sample.company_industry}")
        print(f"Extracted Headline   : {sample.headline}")
        print(f"Document Summary Size: {len(sample.summary)} characters")
        print(f"Source URL Reference : {sample.url}")