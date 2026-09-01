import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import psycopg2
from config import DB_CONFIG

def get_connection():
    """Connects to PostgreSQL database
    
    Returns:
        An active psycopg2 connection object
    """
    return psycopg2.connect(**DB_CONFIG)

def create_table_if_not_exists(conn):
    """Creates the kb_chunks table if it doesn't already exist.

    Args:
        conn: an active PostgreSQL connection
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kb_chunks(
            id SERIAL PRIMARY KEY,
            text TEXT,
            source VARCHAR(255),
            chunk_index INTEGER,
            embedding VECTOR(3072)
        )
    """)
    conn.commit()
    cursor.close()

def insert_chunks(conn, chunks: list):
    """Inserts a list of chunks into the kb_chunks table.

    Args:
        conn: an active PostgreSQL connection
        chunks: list of chunk dicts, each with text, source,
            chunk_index, and embedding keys
    """
    cursor = conn.cursor()
    for chunk in chunks:
        cursor.execute("""
            INSERT INTO kb_chunks(text, source, chunk_index, embedding)
            VALUES (%s, %s, %s, %s)
        """, (chunk["text"], chunk["source"], chunk["chunk_index"], chunk["embedding"]))
    conn.commit()
    cursor.close()

if __name__ == "__main__":
    from document_loader import load_documents_from_folder
    from chunking import chunk_documents
    from embeddings import add_embeddings_to_chunks

docs = load_documents_from_folder("wfm-agent-project/data/kb_documents")
chunks = chunk_documents(docs)
chunks_with_embeddings = add_embeddings_to_chunks(chunks)

conn = get_connection()
create_table_if_not_exists(conn)
insert_chunks(conn, chunks_with_embeddings)
conn.close()

print(f"Inserted {len(chunks_with_embeddings)} chunks into the database.")