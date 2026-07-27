"""
Tool definitions and implementations for the doc QA agent.

Documents are loaded and chunked once via `configure_docs()`, then queried
through simple keyword-overlap scoring (no embeddings or vector DB required,
so the template runs with zero extra infrastructure).
"""

import json
import re
from pathlib import Path
from typing import Any

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

_CHUNKS: list[dict[str, Any]] = []
_DOC_NAMES: list[str] = []


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _chunk_text(text: str, source: str) -> list[dict[str, Any]]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        piece = text[start:end]
        if piece.strip():
            chunks.append({"source": source, "text": piece})
        start = end - CHUNK_OVERLAP
    return chunks


def configure_docs(docs_dir: str) -> int:
    """Load and chunk every .txt/.pdf file in docs_dir. Returns the doc count."""
    global _CHUNKS, _DOC_NAMES
    _CHUNKS = []
    _DOC_NAMES = []

    folder = Path(docs_dir)
    if not folder.is_dir():
        return 0

    for path in sorted(folder.iterdir()):
        if path.suffix.lower() == ".txt":
            text = path.read_text(errors="ignore")
        elif path.suffix.lower() == ".pdf":
            text = _read_pdf(path)
        else:
            continue
        _DOC_NAMES.append(path.name)
        _CHUNKS.extend(_chunk_text(text, path.name))

    return len(_DOC_NAMES)


TOOL_DEFINITIONS = [
    {
        "name": "list_documents",
        "description": "List the documents available in the target folder.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "retrieve_chunks",
        "description": (
            "Search the loaded documents for passages relevant to a query and "
            "return the top matching chunks along with their source document."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query derived from the user's question.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to return.",
                },
            },
            "required": ["query"],
        },
    },
]


def list_documents() -> dict[str, Any]:
    return {"documents": _DOC_NAMES, "count": len(_DOC_NAMES)}


def _score(chunk_text: str, query_terms: list[str]) -> int:
    lowered = chunk_text.lower()
    return sum(lowered.count(term) for term in query_terms)


def retrieve_chunks(query: str, top_k: int = 4) -> dict[str, Any]:
    if not _CHUNKS:
        return {"error": "No documents loaded. Check that --docs points at a folder with .txt or .pdf files."}

    query_terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    scored = [(c, _score(c["text"], query_terms)) for c in _CHUNKS]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    top = [c for c, score in scored[:top_k] if score > 0]
    if not top:
        top = [c for c, _ in scored[:top_k]]

    return {
        "query": query,
        "chunks": [{"source": c["source"], "text": c["text"]} for c in top],
    }


def dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "list_documents":
        result = list_documents()
    elif tool_name == "retrieve_chunks":
        result = retrieve_chunks(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, indent=2)
