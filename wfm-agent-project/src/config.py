from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash-lite"

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "postgres",
    "user": "postgres",
    "password": "parola123"
}

print("Cheie încărcată:", "DA" if GEMINI_API_KEY else "NU")