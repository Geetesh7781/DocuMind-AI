from app.ingest import chunk_words


def test_chunk_overlap_and_coverage():
    text = " ".join(str(i) for i in range(500))
    chunks = chunk_words(text, 100, 20)
    assert chunks[0].split()[-20:] == chunks[1].split()[:20]
    assert chunks[-1].split()[-1] == "499"


def test_short_text_single_chunk():
    assert chunk_words("hello world", 100, 20) == ["hello world"]
