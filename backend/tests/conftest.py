"""Shared fixtures for RAGDocs tests."""

import sys
import pytest
from unittest.mock import MagicMock, AsyncMock


def _build_mock_rag_engine():
    """Create a mock RAGEngine with all expected methods."""
    engine = MagicMock()
    engine.has_documents.return_value = False
    engine.list_documents.return_value = []
    engine.delete_document.return_value = False
    engine.get_document_text.return_value = None
    engine.ingest_document = AsyncMock()
    engine.query = AsyncMock()
    engine.query_stream = AsyncMock()
    return engine


@pytest.fixture()
def client():
    """FastAPI test client with fully mocked RAG engine."""
    mock_engine = _build_mock_rag_engine()

    # Mock LangChain modules before importing main
    sys.modules.setdefault("langchain_google_genai", MagicMock())
    sys.modules.setdefault("langchain_chroma", MagicMock())
    sys.modules.setdefault("langchain.chains", MagicMock())
    sys.modules.setdefault("langchain_core.prompts", MagicMock())
    sys.modules.setdefault("langchain_core.messages", MagicMock())

    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        import app.main as main_module
        main_module.rag_engine = mock_engine
        c._mock_engine = mock_engine
        yield c
