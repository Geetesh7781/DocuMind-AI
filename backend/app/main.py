from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import ingest, llm, store
from .config import settings

app = FastAPI(title="DocuMind AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    doc_ids: list[str] | None = None


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider, "documents": len(store.list_documents())}


@app.get("/api/documents")
def documents():
    return store.list_documents()


@app.post("/api/documents", status_code=201)
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB.")
    try:
        pages = ingest.extract_pages(data)
    except Exception:
        raise HTTPException(400, "Could not read this PDF. It may be corrupted or encrypted.")
    chunks = list(ingest.build_chunks(pages, settings.chunk_words, settings.chunk_overlap))
    if not chunks:
        raise HTTPException(422, "No selectable text found. Scanned PDFs need OCR first.")
    doc_id = store.add_document(file.filename, chunks)
    return {"id": doc_id, "filename": file.filename, "pages": len(pages), "chunks": len(chunks)}


@app.delete("/api/documents/{doc_id}", status_code=204)
def remove(doc_id: str):
    store.delete_document(doc_id)


@app.post("/api/chat")
def chat(req: ChatRequest):
    hits = store.search(req.question, settings.top_k, req.doc_ids)
    if not hits:
        return {"answer": "Upload a document first, then ask a question about it.", "sources": []}
    answer = llm.generate(req.question, hits)
    return {"answer": answer, "sources": hits}
