from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#Definim o functie Python normala - asta e "tool-ul"
def calculeaza_pret_total(pret_unitar:float, cantitate:int) -> float:
    """Calculează prețul total pentru un produs, dat fiind prețul unitar și cantitatea.

    Args:
        pret_unitar: prețul unui singur produs, în RON
        cantitate: numărul de bucăți comandate
    """
    return pret_unitar * cantitate

# Creăm chat-ul, dar de data asta îi spunem ce tool-uri are la dispoziție
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(system_instruction="Ești un asistent care ajută la calcule pentru comenzi.",
                                       tools=[calculeaza_pret_total], #aici ii dam acces la functie
                                       ),
)

response = chat.send_message("Un client a comandat 7 bucăți dintr-un produs care costă 25.5 RON bucata. Cât costă total?")

print("Model:", response.text)