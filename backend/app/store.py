"""ChromaDB vector store wrapper (local embeddings, cosine similarity)."""
import uuid
from collections import defaultdict

import chromadb
from chromadb.utils import embedding_functions

from .config import settings

_client = chromadb.PersistentClient(path=f"{settings.data_dir}/chroma")
_collection = _client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_functions.DefaultEmbeddingFunction(),  # all-MiniLM-L6-v2
    metadata={"hnsw:space": "cosine"},
)


def add_document(filename: str, chunks: list[tuple[int, str]]) -> str:
    doc_id = uuid.uuid4().hex[:12]
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    _collection.add(
        ids=ids,
        documents=[c for _, c in chunks],
        metadatas=[{"doc_id": doc_id, "filename": filename, "page": p} for p, _ in chunks],
    )
    return doc_id


def list_documents() -> list[dict]:
    data = _collection.get(include=["metadatas"])
    docs: dict[str, dict] = defaultdict(lambda: {"chunks": 0, "pages": set()})
    for m in data["metadatas"]:
        d = docs[m["doc_id"]]
        d.update(id=m["doc_id"], filename=m["filename"])
        d["chunks"] += 1
        d["pages"].add(m["page"])
    return [
        {"id": d["id"], "filename": d["filename"], "chunks": d["chunks"], "pages": len(d["pages"])}
        for d in docs.values()
    ]


def delete_document(doc_id: str) -> None:
    _collection.delete(where={"doc_id": doc_id})


def search(question: str, k: int, doc_ids: list[str] | None = None) -> list[dict]:
    if _collection.count() == 0:
        return []
    where = None
    if doc_ids:
        where = {"doc_id": doc_ids[0]} if len(doc_ids) == 1 else {"doc_id": {"$in": doc_ids}}
    res = _collection.query(query_texts=[question], n_results=k, where=where)
    hits = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({
            "text": text,
            "doc_id": meta["doc_id"],
            "filename": meta["filename"],
            "page": meta["page"],
            "score": round(max(0.0, 1 - dist), 3),
        })
    return hits
