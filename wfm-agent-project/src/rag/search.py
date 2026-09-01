import sys
from pathlib import Path

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

if __name__ == "__main__":
    results = search("What is the SLA target for LOB 1?")
    for text, source, chunk_index, distance in results:
        print(f"Distance: {distance:.4f} | Source: {source} | Chunk {chunk_index}")
        print(text[:200])
        print()
  