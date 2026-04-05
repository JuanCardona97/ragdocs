"""
RAGDocs — Backend API
Chat with any document using RAG (Retrieval-Augmented Generation)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from app.models import ChatRequest, ChatResponse, DocumentInfo, UploadResponse
from app.rag_engine import RAGEngine
from app.config import settings


rag_engine: RAGEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG engine on startup."""
    global rag_engine
    rag_engine = RAGEngine()
    yield
    rag_engine = None


app = FastAPI(
    title="RAGDocs",
    description="Chat with any document using AI-powered RAG",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": settings.LLM_MODEL}


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document (PDF, DOCX, or TXT)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_extensions = {".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx"}
    extension = "." + file.filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{extension}' not supported. Use: {', '.join(allowed_extensions)}",
        )

    content = await file.read()

    try:
        doc_info = await rag_engine.ingest_document(
            content=content,
            filename=file.filename,
            file_type=extension,
        )
        return UploadResponse(
            message=f"Document '{file.filename}' processed successfully",
            document=doc_info,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Ask a question about the uploaded documents."""
    if not rag_engine.has_documents():
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded yet. Upload a document first.",
        )

    try:
        answer, sources = await rag_engine.query(
            question=request.question,
            document_id=request.document_id,
            chat_history=request.chat_history,
        )
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {e}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream an answer about the uploaded documents via SSE."""
    if not rag_engine.has_documents():
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded yet. Upload a document first.",
        )

    return StreamingResponse(
        rag_engine.query_stream(
            question=request.question,
            document_id=request.document_id,
            chat_history=request.chat_history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    """List all uploaded documents."""
    return rag_engine.list_documents()


@app.get("/documents/{document_id}/preview")
async def preview_document(document_id: str):
    """Get the extracted text of a document for preview."""
    text = rag_engine.get_document_text(document_id)
    if text is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": document_id, "text": text}


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings."""
    success = rag_engine.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document {document_id} deleted successfully"}
