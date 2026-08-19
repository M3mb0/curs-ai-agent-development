from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(system_instruction="Ești un asistent util. Răspunde concis, în română."
                                       ),
)

print("Chat pornit! Scrie 'exit' ca să ieși.\n")

while True:
    user_input = input("Tu: ")

    if user_input.lower() == "exit":
        print("La revedere")
        break

    response = chat.send_message(user_input)
    print("Model", response.text)
    print()