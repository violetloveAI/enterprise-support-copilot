from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    section: str
    category: str
    content: str
    score: float = Field(ge=0, le=1)
    source_path: str
