from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from ..core.config import Settings


def parse_markdown(path: Path) -> tuple[dict[str, str], list[tuple[str, str]]]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    if text.startswith("---"):
        _, frontmatter, text = text.split("---", 2)
        for line in frontmatter.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"')
    sections: list[tuple[str, str]] = []
    heading = metadata.get("title", path.stem)
    buffer: list[str] = []
    for line in text.strip().splitlines():
        if line.startswith("## "):
            if buffer:
                sections.append((heading, "\n".join(buffer).strip()))
            heading, buffer = line[3:].strip(), []
        elif not line.startswith("# "):
            buffer.append(line)
    if buffer:
        sections.append((heading, "\n".join(buffer).strip()))
    return metadata, [(heading, content) for heading, content in sections if content]


def chunk_text(content: str, size: int = 700, overlap: int = 80) -> list[str]:
    if len(content) <= size:
        return [content]
    sentences = [part.strip() for part in re.split(r"(?<=[。！？\n])", content) if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) > size:
            chunks.append(current)
            current = current[-overlap:] + sentence
        else:
            current += sentence
    if current:
        chunks.append(current)
    return chunks


def load_documents(knowledge_path: Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(knowledge_path.glob("*.md")):
        meta, sections = parse_markdown(path)
        doc_id = meta["doc_id"]
        chunk_number = 0
        for section, content in sections:
            for chunk in chunk_text(content):
                chunk_number += 1
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "doc_id": doc_id,
                            "chunk_id": f"{doc_id}#C{chunk_number:02d}",
                            "title": meta.get("title", path.stem),
                            "section": section,
                            "category": meta.get("category", "general"),
                            "source_path": str(path),
                        },
                    )
                )
    return documents


def build_index(settings: Settings, reset: bool = True) -> int:
    documents = load_documents(settings.knowledge_base_path)
    settings.chroma_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = settings.chroma_path.parent / "knowledge_manifest.json"
    manifest.write_text(
        json.dumps(
            [{"content": item.page_content, "metadata": item.metadata} for item in documents],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if settings.retrieval_provider == "lexical":
        return len(documents)
    settings.validate_runtime()
    if reset and settings.chroma_path.exists():
        shutil.rmtree(settings.chroma_path)
    from langchain_chroma import Chroma

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.effective_embedding_api_key,
        base_url=settings.effective_embedding_base_url,
    )
    Chroma.from_documents(
        documents,
        embedding=embeddings,
        persist_directory=str(settings.chroma_path),
        collection_name="expense_support_kb",
    )
    return len(documents)
