from google import genai
from dotenv import load_dotenv
import os

#Incarca variabilele din fisierul .env
load_dotenv()

#Creeaza clientul, folosind cheia din .env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#Primul apel catre model
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents = "Explica-mi in 2 propozitii ce este un AI agent"
)

print(response.text)