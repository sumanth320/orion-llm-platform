import os
import uuid

import chromadb
from sentence_transformers import SentenceTransformer


DATA_FOLDER = "data/docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="docs")


def load_documents():
    documents = []

    for filename in os.listdir(DATA_FOLDER):
        filepath = os.path.join(DATA_FOLDER, filename)

        if not filename.endswith(".txt"):
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        documents.append({
            "doc_id": filename,
            "content": text
        })

    return documents


def chunk_document(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def index_documents():
    documents = load_documents()

    for doc in documents:
        doc_id = doc["doc_id"]

        chunks = chunk_document(doc["content"])

        print(f"Processing {doc_id} | chunks={len(chunks)}")

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{idx}"

            embedding = model.encode(chunk).tolist()

            metadata = {
                "doc_id": doc_id,
                "chunk_id": chunk_id
            }

            collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[metadata]
            )

    print("Indexing complete")


if __name__ == "__main__":
    index_documents()
