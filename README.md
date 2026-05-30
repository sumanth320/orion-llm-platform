# Orion LLM Platform

FastAPI + Streamlit project for a finance assistant that can:
- route queries (`direct`, `rag`, `tool`)
- fetch stock quotes via Finnhub
- retrieve local docs from ChromaDB
- generate responses using a local Ollama model

## Project Structure

Key folders:
- `app/main.py` - FastAPI entrypoint
- `app/api/` - HTTP routes, schemas, handlers
- `app/orchestration/` - routing, decision engine, execution flow
- `app/services/` - LLM and tool integrations
- `app/retrieval/` - RAG retrieval/indexing logic
- `ui/streamlit_app.py` - Streamlit frontend
- `data/docs/` - source docs for indexing
- `chroma_db/` - local vector DB persistence

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Ollama installed and running locally
- A Finnhub API key

## Setup

### 1) Create virtual environment and install dependencies

```zsh
cd ./orion-llm-platform
uv venv .venv
uv pip install --python .venv/bin/python -r app/requirements.txt
```

### 2) Activate environment

```zsh
cd ./orion-llm-platform
source .venv/bin/activate
```

### 3) Configure environment variables

Create a `.env` file in repo root:

```env
FINNHUB_API_KEY=your_finnhub_api_key_here
# Optional: improves Hugging Face download limits
# HF_TOKEN=your_hf_token_here
```

### 4) Ensure Ollama model is available

```zsh
ollama pull llama3:latest
```

## Running the App

Run in two terminals.

### Terminal A: FastAPI backend

Use source-folder reload to avoid `.venv` watcher loops.

```zsh
cd ./orion-llm-platform
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app --reload-dir tests
```

Backend URLs:
- API: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

### Terminal B: Streamlit frontend

```zsh
cd ./orion-llm-platform
source .venv/bin/activate
streamlit run ui/streamlit_app.py
```

Frontend URL:
- `http://localhost:8501`

## Optional: Index Documents for RAG

If you update files in `data/docs/`, run indexing:

```zsh
cd ./orion-llm-platform
source .venv/bin/activate
python app/retrieval/index_documents.py
```

## Quick API Test

```zsh
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"how is credo stock doing","user_id":"demo-user","session_id":"s1"}'
```

## Troubleshooting

- `--reload` keeps restarting:
  - Use `--reload-dir app --reload-dir tests` so watcher does not track `.venv`.
- Tool route returns clarify often:
  - Check `FINNHUB_API_KEY` is set and valid.
- Slow startup with transformer messages:
  - First run can download model artifacts; subsequent runs are faster.
- Ollama errors:
  - Ensure Ollama service is running and `llama3:latest` is present.

## Current Tech Stack

- FastAPI + Uvicorn
- Streamlit
- SentenceTransformers
- ChromaDB
- Ollama
- Requests + python-dotenv
