"""Tests for document processing and chunking."""

import pytest
from app.embeddings import DocumentProcessor

processor = DocumentProcessor()


# ── Text extraction ──

def test_extract_plain_text():
    content = b"Hello, this is a plain text document."
    text = processor.extract_text(content, ".txt")
    assert text == "Hello, this is a plain text document."


def test_extract_markdown():
    content = b"# Title\n\nSome **bold** text."
    text = processor.extract_text(content, ".md")
    assert "# Title" in text
    assert "**bold**" in text


def test_extract_csv():
    content = b"name,age,city\nAlice,30,NYC\nBob,25,LA"
    text = processor.extract_text(content, ".csv")
    assert "name: Alice" in text
    assert "age: 30" in text
    assert "city: NYC" in text
    assert "name: Bob" in text


def test_extract_csv_with_empty_values():
    content = b"name,age\nAlice,\nBob,25"
    text = processor.extract_text(content, ".csv")
    assert "name: Alice" in text
    assert "name: Bob" in text


def test_extract_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported"):
        processor.extract_text(b"data", ".xyz")


def test_extract_empty_document():
    with pytest.raises(ValueError, match="No text"):
        processor.extract_text(b"   ", ".txt")


def test_extract_empty_bytes():
    with pytest.raises(ValueError, match="No text"):
        processor.extract_text(b"", ".txt")


def test_extract_unicode_text():
    content = "Texto con acentos: café, niño, über".encode("utf-8")
    text = processor.extract_text(content, ".txt")
    assert "café" in text
    assert "niño" in text


# ── Chunking ──

def test_split_into_chunks_basic():
    text = "word " * 500  # 2500 characters
    chunks = processor.split_into_chunks(text, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 1000


def test_split_into_chunks_short_text():
    text = "Short text that fits in one chunk."
    chunks = processor.split_into_chunks(text, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_into_chunks_overlap():
    text = "Section A. " * 100 + "Section B. " * 100
    chunks = processor.split_into_chunks(text, chunk_size=500, chunk_overlap=100)
    assert len(chunks) >= 3


def test_chunk_size_parameter():
    text = "x" * 3000
    small_chunks = processor.split_into_chunks(text, chunk_size=500, chunk_overlap=50)
    large_chunks = processor.split_into_chunks(text, chunk_size=1500, chunk_overlap=50)
    assert len(small_chunks) > len(large_chunks)


def test_split_preserves_all_content():
    text = "The quick brown fox jumps over the lazy dog. " * 50
    chunks = processor.split_into_chunks(text, chunk_size=200, chunk_overlap=0)
    combined = "".join(chunks)
    # All words from original should be present
    assert "quick" in combined
    assert "lazy" in combined


def test_split_respects_separators():
    text = "Paragraph one about topic A.\n\nParagraph two about topic B.\n\nParagraph three about topic C."
    chunks = processor.split_into_chunks(text, chunk_size=50, chunk_overlap=0)
    # Should split on paragraph boundaries
    assert len(chunks) >= 2
