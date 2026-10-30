"""PDF text extraction and overlap-aware chunking."""
from io import BytesIO

from pypdf import PdfReader


def extract_pages(data: bytes) -> list[tuple[int, str]]:
    reader = PdfReader(BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        if text:
            pages.append((i, text))
    return pages


def chunk_words(text: str, size: int, overlap: int) -> list[str]:
    if size <= overlap:
        raise ValueError("chunk size must be larger than overlap")
    words = text.split()
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        piece = words[start:start + size]
        if piece:
            chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
    return chunks


def build_chunks(pages: list[tuple[int, str]], size: int, overlap: int):
    """Yield (page_number, chunk_text). Chunks never cross page boundaries so
    every citation maps to exactly one page."""
    for page_no, text in pages:
        for chunk in chunk_words(text, size, overlap):
            yield page_no, chunk
