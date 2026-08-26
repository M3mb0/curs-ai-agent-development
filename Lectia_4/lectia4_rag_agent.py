from google import genai
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

conn = psycopg2.connect(
    host="localhost", port="5432", database="postgres",
    user="postgres", password="parola123"
)
cursor = conn.cursor()

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

    cursor.execute("""
        SELECT text, source, chunk_index, embedding <=> %s::vector AS distance
        FROM document_chunks
        ORDER BY distance
        LIMIT %s
    """, (query_embedding, top_k))

    results = cursor.fetchall()
    return results

def answer_with_context(query: str) -> str:
    """A generated answer based on the retrieved contex
    
    Args:
        query: the search question, in natural language

    Returns:
        An exact answer based on the information received

    """
    results = search(query)
    context = ""
    for text, source, chunk_index, distance in results:
        context += text
    
    # Pasul 2: construiești un text/prompt care combină chunk-urile + întrebarea
    
    response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents = f"Based on this context: {context}\n\nAnswer this question: {query}"
                )
    
    return response.text

result1 = answer_with_context("What programming languages does this person know?")
print(result1)
print("---")

result2 = answer_with_context("What customer support experience does this person have?")
print(result2)
print("---")

result3 = answer_with_context("What languages does this person speak?")
print(result3)

cursor.close()
conn.close()    