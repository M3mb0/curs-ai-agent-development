"""Tests for RAG components that don't require external API calls:
document loading and text chunking.
"""


import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from rag.document_loader import load_documents_from_folder
from rag.chunking import count_tokens, split_with_overlap, chunk_documents


def test_count_tokens():
    """Tests that count_tokens returns a positive number for a
    non-empty text.
    """
    text = "Hello world, this is a test."
    result = count_tokens(text)
    assert result > 0


def test_split_with_overlap():
    """Tests that split_with_overlap divides a long text into more
    than one chunk.
    """
    long_text = "word " * 500  # text lung, repetitiv, pentru test simplu
    chunks = split_with_overlap(long_text, dimension=100, overlap=20, source="test.md")

    assert len(chunks) > 1


def test_load_documents_from_folder():
    """Tests that load_documents_from_folder returns a non-empty list
    of dicts, each containing 'filename' and 'text' keys.
    """
    documents = load_documents_from_folder("wfm-agent-project/data/kb_documents")

    assert len(documents) > 0
    assert "filename" in documents[0]
    assert "text" in documents[0]