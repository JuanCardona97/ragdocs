"""
RAG Engine — Core retrieval-augmented generation pipeline.

Handles document ingestion, embedding, storage, and querying
using LangChain + ChromaDB + Google Gemini.
"""

import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from app.embeddings import DocumentProcessor
from app.models import DocumentInfo, SourceChunk
from app.config import settings


SYSTEM_TEMPLATE = """You are RAGDocs, a helpful assistant that answers questions
based strictly on the provided document context.

Rules:
- Only answer based on the context below. If the answer is not in the context,
  say "I couldn't find this information in the uploaded documents."
- Cite specific sections when possible.
- Be concise but thorough.
- If the question is ambiguous, ask for clarification.
- Take into account the conversation history for follow-up questions.

Context from documents:
{context}"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_TEMPLATE),
    MessagesPlaceholder("chat_history"),
    ("human", "{question}"),
])


class RAGEngine:
    """Manages the full RAG pipeline: ingest → embed → store → retrieve → generate."""

    def __init__(self):
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self._llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            temperature=settings.TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self._vectorstore = Chroma(
            collection_name="ragdocs",
            embedding_function=self._embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
        self._processor = DocumentProcessor()
        self._documents: dict[str, DocumentInfo] = {}
        self._document_texts: dict[str, str] = {}

    async def ingest_document(
        self,
        content: bytes,
        filename: str,
        file_type: str,
    ) -> DocumentInfo:
        """Process a document: extract text, chunk, embed, and store."""
        doc_id = str(uuid.uuid4())[:8]

        raw_text = self._processor.extract_text(content, file_type)

        chunks = self._processor.split_into_chunks(
            text=raw_text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        metadatas = [
            {
                "document_id": doc_id,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        self._vectorstore.add_texts(
            texts=chunks,
            metadatas=metadatas,
            ids=ids,
        )

        doc_info = DocumentInfo(
            id=doc_id,
            filename=filename,
            file_type=file_type,
            chunks=len(chunks),
            characters=len(raw_text),
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        self._documents[doc_id] = doc_info
        self._document_texts[doc_id] = raw_text

        return doc_info

    def _get_retriever(self, document_id: str | None = None):
        """Build a retriever with optional document filter."""
        search_kwargs = {"k": settings.TOP_K_RESULTS}
        if document_id:
            search_kwargs["filter"] = {"document_id": document_id}

        return self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs,
        )

    def _build_context(self, docs) -> tuple[str, list[SourceChunk]]:
        """Build context string and source list from retrieved documents."""
        context_parts = []
        sources = []
        for doc in docs:
            context_parts.append(doc.page_content)
            sources.append(
                SourceChunk(
                    content=doc.page_content[:300],
                    filename=doc.metadata.get("filename", "unknown"),
                    chunk_index=doc.metadata.get("chunk_index", 0),
                )
            )
        return "\n\n".join(context_parts), sources

    async def query(
        self,
        question: str,
        document_id: str | None = None,
        chat_history: list[dict] | None = None,
    ) -> tuple[str, list[SourceChunk]]:
        """Query the knowledge base and generate an answer."""
        retriever = self._get_retriever(document_id)
        docs = retriever.invoke(question)
        context, sources = self._build_context(docs)

        # Convert chat history to LangChain messages
        messages = []
        for msg in (chat_history or []):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        prompt_value = PROMPT.invoke({
            "context": context,
            "chat_history": messages,
            "question": question,
        })

        result = self._llm.invoke(prompt_value)
        return result.content, sources

    async def query_stream(
        self,
        question: str,
        document_id: str | None = None,
        chat_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream the answer token by token via SSE."""
        retriever = self._get_retriever(document_id)
        docs = retriever.invoke(question)
        context, sources = self._build_context(docs)

        # Convert chat history to LangChain messages
        messages = []
        for msg in (chat_history or []):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        prompt_value = PROMPT.invoke({
            "context": context,
            "chat_history": messages,
            "question": question,
        })

        # Send sources first
        sources_data = [s.model_dump() for s in sources]
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources_data})}\n\n"

        # Stream tokens
        async for chunk in self._llm.astream(prompt_value):
            if chunk.content:
                yield f"data: {json.dumps({'type': 'token', 'token': chunk.content})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    def has_documents(self) -> bool:
        return len(self._documents) > 0

    def list_documents(self) -> list[DocumentInfo]:
        return list(self._documents.values())

    def delete_document(self, document_id: str) -> bool:
        if document_id not in self._documents:
            return False

        doc_info = self._documents[document_id]
        ids_to_delete = [
            f"{document_id}_chunk_{i}" for i in range(doc_info.chunks)
        ]
        self._vectorstore.delete(ids=ids_to_delete)

        del self._documents[document_id]
        self._document_texts.pop(document_id, None)
        return True

    def get_document_text(self, document_id: str) -> str | None:
        return self._document_texts.get(document_id)
