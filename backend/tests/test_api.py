"""Tests for FastAPI endpoints."""

import io
import json
from unittest.mock import AsyncMock
from app.models import DocumentInfo, SourceChunk


def _make_doc_info(**overrides):
    defaults = dict(
        id="abc123",
        filename="test.txt",
        file_type=".txt",
        chunks=3,
        characters=1500,
        uploaded_at="2026-01-01T00:00:00+00:00",
    )
    defaults.update(overrides)
    return DocumentInfo(**defaults)


# ── Health ──

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data


# ── Upload ──

def test_upload_unsupported_file_type(client):
    file = io.BytesIO(b"data")
    response = client.post(
        "/documents/upload",
        files={"file": ("image.png", file, "image/png")},
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_upload_txt_document(client):
    doc = _make_doc_info(filename="test.txt")
    client._mock_engine.ingest_document = AsyncMock(return_value=doc)

    content = b"This is a test document with enough content to process."
    response = client.post(
        "/documents/upload",
        files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document"]["filename"] == "test.txt"
    assert data["document"]["file_type"] == ".txt"
    client._mock_engine.ingest_document.assert_called_once()


def test_upload_pdf_accepted(client):
    doc = _make_doc_info(filename="report.pdf", file_type=".pdf")
    client._mock_engine.ingest_document = AsyncMock(return_value=doc)

    response = client.post(
        "/documents/upload",
        files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["document"]["filename"] == "report.pdf"


def test_upload_csv_accepted(client):
    doc = _make_doc_info(filename="data.csv", file_type=".csv")
    client._mock_engine.ingest_document = AsyncMock(return_value=doc)

    response = client.post(
        "/documents/upload",
        files={"file": ("data.csv", io.BytesIO(b"a,b\n1,2"), "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["document"]["filename"] == "data.csv"


def test_upload_no_filename(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("", io.BytesIO(b"data"), "text/plain")},
    )
    assert response.status_code in (400, 422)


# ── List Documents ──

def test_list_documents_empty(client):
    client._mock_engine.list_documents.return_value = []
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_list_documents_after_upload(client):
    doc = _make_doc_info(filename="report.pdf")
    client._mock_engine.list_documents.return_value = [doc]

    response = client.get("/documents")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["filename"] == "report.pdf"


# ── Delete ──

def test_delete_document(client):
    client._mock_engine.delete_document.return_value = True
    response = client.delete("/documents/abc123")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]


def test_delete_nonexistent_document(client):
    client._mock_engine.delete_document.return_value = False
    response = client.delete("/documents/nonexistent-id")
    assert response.status_code == 404


# ── Preview ──

def test_preview_document(client):
    client._mock_engine.get_document_text.return_value = "Hello world content"
    response = client.get("/documents/abc123/preview")
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Hello world content"
    assert data["document_id"] == "abc123"


def test_preview_document_not_found(client):
    client._mock_engine.get_document_text.return_value = None
    response = client.get("/documents/nonexistent/preview")
    assert response.status_code == 404


# ── Chat ──

def test_chat_without_documents(client):
    client._mock_engine.has_documents.return_value = False
    response = client.post("/chat", json={"question": "What is this about?"})
    assert response.status_code == 400
    assert "No documents" in response.json()["detail"]


def test_chat_with_documents(client):
    client._mock_engine.has_documents.return_value = True
    client._mock_engine.query = AsyncMock(
        return_value=("The answer is 42.", [])
    )
    response = client.post("/chat", json={"question": "What is the answer?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The answer is 42."
    assert data["sources"] == []


def test_chat_with_sources(client):
    client._mock_engine.has_documents.return_value = True
    sources = [SourceChunk(content="chunk text", filename="doc.pdf", chunk_index=0)]
    client._mock_engine.query = AsyncMock(
        return_value=("Answer with sources.", sources)
    )
    response = client.post("/chat", json={"question": "Tell me more"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) == 1
    assert data["sources"][0]["filename"] == "doc.pdf"


def test_chat_with_document_id_filter(client):
    client._mock_engine.has_documents.return_value = True
    client._mock_engine.query = AsyncMock(return_value=("Filtered answer.", []))
    response = client.post(
        "/chat",
        json={"question": "What?", "document_id": "doc123"},
    )
    assert response.status_code == 200
    call_kwargs = client._mock_engine.query.call_args
    assert call_kwargs[1]["document_id"] == "doc123" or call_kwargs[0][1] == "doc123"


def test_chat_with_history(client):
    client._mock_engine.has_documents.return_value = True
    client._mock_engine.query = AsyncMock(return_value=("Follow-up answer.", []))
    history = [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
    ]
    response = client.post(
        "/chat",
        json={"question": "Follow-up?", "chat_history": history},
    )
    assert response.status_code == 200


def test_chat_invalid_request(client):
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_empty_question(client):
    response = client.post("/chat", json={"question": ""})
    assert response.status_code == 422


# ── Stream ──

def test_stream_without_documents(client):
    client._mock_engine.has_documents.return_value = False
    response = client.post("/chat/stream", json={"question": "Hello?"})
    assert response.status_code == 400
