# 1. Use a lightweight, official base image
FROM python:3.11-slim

# Allow slower model downloads during image build.
ENV HF_HUB_DOWNLOAD_TIMEOUT=120 \
	HF_HUB_ETAG_TIMEOUT=60 \
	FASTEMBED_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2 \
	FASTEMBED_CACHE_DIR=/app/.cache/fastembed

# 2. Install uv directly inside the container for lightning-fast package resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Set up an isolated working directory inside the container
WORKDIR /app

# 4. Copy over our unified dependency manifest
COPY requirements.txt .

RUN mkdir -p /app/.cache/fastembed

# 5. Compile and install dependencies globally inside the container using uv
# We use --system because the container itself acts as our isolated environment
RUN uv pip install --system --no-cache -r requirements.txt

# 5b. Warm the embedding model cache during build so the runtime container does not
# need to download from Hugging Face when the Airflow task starts.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2', cache_dir='/app/.cache/fastembed', threads=1)"

# 6. Copy over the local ingestion source code
COPY ingestion/ ./ingestion/

# 7. Define the immutable execution command for our pipeline pod
CMD ["python", "ingestion/ingestion_pipeline.py"]