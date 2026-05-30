from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="docs")


def retrieve(query: str, top_k: int = 10):
    query_emb = model.encode([query])[0]

    results = collection.query(
        query_embeddings=[query_emb.tolist()],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for i in range(len(docs)):
        chunks.append({
            "chunk": docs[i],
            "score": 1 - distances[i],
            "doc_id": metas[i].get("doc_id"),
            "chunk_id": metas[i].get("chunk_id"),
            "metadata": metas[i]
        })

    return chunks