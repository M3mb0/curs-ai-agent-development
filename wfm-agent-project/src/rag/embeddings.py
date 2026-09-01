import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def get_embedding(text: str) -> list:
    """Converts a piece of text into an embedding vector using Gemini.

    Args:
        text: the text to convert into a vector

    Returns:
        A list of floats (the embedding), representing the semantic
        meaning of the text.
    """
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


def get_embedding_with_retry(text: str, max_retries: int = 5) -> list:
    """Gets an embedding, retrying with increasing wait time if rate-limited.

    Args:
        text: the text to convert into a vector
        max_retries: how many times to retry before giving up

    Returns:
        A list of floats (the embedding)
    """
    for attempt in range(max_retries):
        try:
            return get_embedding(text)
        except Exception as e:
            wait_time = 20 * (attempt + 1)
            print(f"Rate limit, retry {attempt + 1}/{max_retries}, waiting {wait_time}s...")
            time.sleep(wait_time)
    raise Exception("Failed after maximum retries")


def add_embeddings_to_chunks(chunks: list) -> list:
    """Adds an embedding vector to each chunk in the list.

    Args:
        chunks: list of chunk dicts (from chunk_documents)

    Returns:
        The same list, with an "embedding" key added to each chunk
    """
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = get_embedding_with_retry(chunk["text"])
        print(f"Procesat chunk {i+1}/{len(chunks)}")
        time.sleep(5)
    return chunks


if __name__ == "__main__":
    from document_loader import load_documents_from_folder
    from chunking import chunk_documents

    docs = load_documents_from_folder("wfm-agent-project/data/kb_documents")
    chunks = chunk_documents(docs)
    chunks_with_embeddings = add_embeddings_to_chunks(chunks)

    print(f"Total chunks: {len(chunks_with_embeddings)}")
    print("Embedding length:", len(chunks_with_embeddings[0]["embedding"]))