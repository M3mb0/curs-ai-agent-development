from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#Cream o sesiune de chat ( asta tine minte istoricul automat)
chat = client.chats.create(model= "gemini-3.6-flash")

#Primul mesaj
response1 = chat.send_message("Ma cheama Cristian si lucrez in domeniul BPO)")
print("Model:", response1.text)

print("---")

#Al doilea mesaj - testam daca isi aminteste
response2 = chat.send_message("Cum ma cheama si in ce domeniu lucrez")
print("Model:", response2.text)