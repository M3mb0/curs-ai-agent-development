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


def add_embeddings_to_chunks(chunks: list) -> list:
    """Adds an embedding vector to each chunk in the list.

    Args:
        chunks: list of chunk dicts (from chunk_documents)

    Returns:
        The same list, with an "embedding" key added to each chunk
    """
    for i, chunk in enumerate(chunks):
        try:
            chunk["embedding"] = get_embedding(chunk["text"])
        except Exception as e:
            print(f"Rate limit atins la chunk {i}, aștept 30 secunde...")
            time.sleep(30)
            chunk["embedding"] = get_embedding(chunk["text"])
        
        print(f"Procesat chunk {i+1}/{len(chunks)}")
        time.sleep(3)
    
    return chunks

if __name__ == "__main__":
    from document_loader import load_documents_from_folder
    from chunking import chunk_documents

    docs = load_documents_from_folder("wfm-agent-project/data/kb_documents")
    chunks = chunk_documents(docs)
    chunks_with_embeddings = add_embeddings_to_chunks(chunks)

    print(f"Total chunks: {len(chunks_with_embeddings)}")
    print("Embedding length:", len(chunks_with_embeddings[0]["embedding"]))