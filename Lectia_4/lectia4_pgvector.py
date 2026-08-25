from google import genai
from dotenv import load_dotenv
import os
import psycopg2
from pypdf import PdfReader
import re

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- Functions from Lecția 3 (reused) ---

def clean_text(text: str) -> str:
    """Cleans extracted text by removing excess whitespace and blank lines.

    Args:
        text: the raw text to clean

    Returns:
        The cleaned text, with at most 2 consecutive blank lines,
        single spaces between words, and no leading/trailing whitespace.
    """
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def split_with_overlap(text: str, size: int, overlap: int) -> list:
    """Splits text into overlapping chunks of a fixed character size.

    Args:
        text: the full text to split
        size: the target size (in characters) of each chunk
        overlap: how many characters each chunk shares with the previous one

    Returns:
        A list of text chunks (strings).
    """
    chunks = []
    for i in range(0, len(text), size - overlap):
        end = i + size
        chunks.append(text[i:end])
    return chunks


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


# --- Table setup (run once, then comment out) ---
# cursor.execute("DROP TABLE document_chunks")
# """Deletes the document_chunks table, including all its data.
# Used only when the table needs to be recreated from scratch
# (e.g. after changing the embedding dimension)."""

# cursor.execute("""
#     CREATE TABLE document_chunks(
#         id SERIAL PRIMARY KEY,
#         text TEXT,
#         source VARCHAR(255),
#         chunk_index INTEGER,
#         embedding VECTOR(3072)
#     )
# """)
# """Creates the document_chunks table, with a column for the text,
# its source document, its position in the document, and its
# embedding vector (dimension 3072, matching Gemini's embedding model)."""
# conn.commit()


# --- Extract and prepare chunks from the CV ---

# reader = PdfReader("Lectia_3/Cristian_Ungureanu_TechSupport_CV.pdf")
# full_text = ""
# for page in reader.pages:
#     full_text += page.extract_text()
# """Extracts raw text from every page of the PDF and concatenates it
# into a single string, full_text."""

# cleaned_text = clean_text(full_text)
# text_chunks = split_with_overlap(cleaned_text, size=500, overlap=50)
# """Cleans the extracted text, then splits it into overlapping chunks
# ready to be embedded and stored."""


# --- Database connection ---

conn = psycopg2.connect(
    host="localhost", port="5432", database="postgres",
    user="postgres", password="parola123"
)
cursor = conn.cursor()


# --- For each chunk: generate embedding and store it ---

# for index, chunk_text in enumerate(text_chunks):
#     embedding = get_embedding(chunk_text)
#     cursor.execute("""
#         INSERT INTO document_chunks (text, source, chunk_index, embedding)
#         VALUES (%s, %s, %s, %s)
#     """, (chunk_text, "Cristian_Ungureanu_TechSupport_CV.pdf", index, embedding))
#     print(f"Chunk {index} inserted, embedding size: {len(embedding)}")
# """For every chunk in text_chunks: generates its embedding, then
# inserts the chunk (text + metadata + embedding) as a new row in
# the document_chunks table."""

# conn.commit()
# print("\nAll chunks inserted successfully!")


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


# Test a search
results = search("What programming languages does this person know?")

for text, source, chunk_index, distance in results:
    print(f"Distance: {distance:.4f} | Chunk {chunk_index}")
    print(text[:200])
    print()

cursor.close()
conn.close()