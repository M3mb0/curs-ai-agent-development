import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent))

from embeddings import get_embedding
from vector_store import get_connection

def search(query: str, top_k: int = 3) -> list:
    """Searches the database for the most semantically similar chunks to a query.
    
        Converts the query text into an embedding, then finds the chunks
        in the database whose embeddings are closest in meaning (smallest
        cosine distance).
    
        Args:
            query: the search question, in natural language
            top_k: how many top results to return (default: 3)
    
        Returns:
            A list of tuples: (text, source, chunk_index, distance)
        """
    query_embedding = get_embedding(query)
    conn = get_connection()
    cursor = conn.cursor() 
    cursor.execute("""
            SELECT text, source, chunk_index, embedding <=> %s::vector AS distance
            FROM kb_chunks
            ORDER BY distance
            LIMIT %s
        """, (query_embedding, top_k))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

_search_cache = {}

def cached_search(query: str, top_k: int = 3) -> list:
    """Returns a cached result for the text, computing and storing it
    if not already cached.

    Args:
        query: the search question, in natural language
        top_k: how many top results to return (default: 3)
    
    Returns:
           A list of tuples: (text, source, chunk_index, distance) — the
        same format returned by search(), either freshly computed or
        retrieved from cache
    """
    cache_key = (query, top_k)
    if cache_key in _search_cache:
        return _search_cache[cache_key]
    _search_cache[cache_key] = search(query, top_k)
    return _search_cache[cache_key]
        

if __name__ == "__main__":
    results = search("What is the SLA target for LOB 1?")
    for text, source, chunk_index, distance in results:
        print(f"Distance: {distance:.4f} | Source: {source} | Chunk {chunk_index}")
        print(text[:200])
        print()


    start = time.time()
    results1 = cached_search("What is the SLA target for LOB 1?")
    print("First call:", time.time() - start, "secunde")
    
    start = time.time()
    results2 = cached_search("What is the SLA target for LOB 1?")
    print("Second call:", time.time() - start, "secunde")