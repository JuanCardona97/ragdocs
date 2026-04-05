"""
API Models — Pydantic schemas for requests and responses.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Question to ask about the uploaded documents",
        examples=["What are the main conclusions of this report?"],
    )
    document_id: str | None = Field(
        default=None,
        description="Optional: filter to a specific document by ID",
    )
    chat_history: list[dict] | None = Field(
        default=None,
        description="Previous messages for multi-turn conversation",
    )


class SourceChunk(BaseModel):
    """A chunk of source text used to generate the answer."""

    content: str = Field(description="Text content of the source chunk")
    filename: str = Field(description="Original filename")
    chunk_index: int = Field(description="Position of the chunk in the document")


class ChatResponse(BaseModel):
    """Response body for the /chat endpoint."""

    answer: str = Field(description="AI-generated answer")
    sources: list[SourceChunk] = Field(
        default_factory=list,
        description="Source chunks used to generate the answer",
    )


class DocumentInfo(BaseModel):
    """Metadata about an uploaded document."""

    id: str
    filename: str
    file_type: str
    chunks: int = Field(description="Number of text chunks created")
    characters: int = Field(description="Total character count")
    uploaded_at: str


class UploadResponse(BaseModel):
    """Response body for the /documents/upload endpoint."""

    message: str
    document: DocumentInfo
