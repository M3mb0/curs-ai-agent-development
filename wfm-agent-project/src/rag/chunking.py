import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count how many tokens are in the text.

    Args:
        text: the text to count tokens for

    Returns:
        The number of tokens
    """
    return len(encoder.encode(text))


def split_with_overlap(text: str, dimension: int, overlap: int, source: str) -> list:
    """Splits a single text into overlapping chunks, with metadata.

    Args:
        text: the full text to split
        dimension: target size (characters) of each chunk
        overlap: how many characters each chunk shares with the previous one
        source: the name of the document this text came from

    Returns:
        A list of dicts, each with text, source, chunk_index, token_count
    """
    chunks = []
    chunk_index = 0
    for i in range(0, len(text), dimension - overlap):
        end = i + dimension
        chunk_text = text[i:end]

        chunk = {
            "text": chunk_text,
            "source": source,
            "chunk_index": chunk_index,
            "token_count": count_tokens(chunk_text)
        }
        chunks.append(chunk)
        chunk_index += 1
    return chunks


def chunk_documents(documents: list, dimension: int = 500, overlap: int = 50) -> list:
    """Chunks multiple documents into a single flat list of chunks.

    Args:
        documents: list of dicts, each with "filename" and "text" keys
        dimension: target size (characters) of each chunk
        overlap: how many characters each chunk shares with the previous one

    Returns:
        A single list containing all chunks from all documents combined
    """
    all_chunks = []

    for doc in documents:
        doc_chunks = split_with_overlap(doc["text"], dimension, overlap, doc["filename"])
        all_chunks.extend(doc_chunks)

    return all_chunks


if __name__ == "__main__":
    from document_loader import load_documents_from_folder

    docs = load_documents_from_folder("wfm-agent-project/data/kb_documents")
    all_chunks = chunk_documents(docs)

    print(f"Total chunks from {len(docs)} documents: {len(all_chunks)}")
    print(all_chunks[0])