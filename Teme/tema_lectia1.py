"""Construiește un script Python (tema_lectia1.py) care simulează un mic "asistent BPO" — ceva relevant pentru domeniul tău. Cerințe:

Creează un system prompt (instrucțiune generală) care spune modelului ceva de genul: "Ești un asistent care ajută un operator de call center. Răspunde scurt, concis, în maxim 3 propoziții."
(Vezi documentația google-genai pentru cum se trimite system prompt — hint: la chats.create() există un parametru config unde poți seta system_instruction)
Creează o sesiune de chat cu memorie
Trimite minim 3 mesaje succesive, care se leagă unele de altele (ex: primul mesaj descrie o situație cu un client nemulțumit, al doilea îl întreabă ce ar răspunde, al treilea cere o variantă mai formală a răspunsului anterior)
Printează fiecare răspuns, clar separat (poți folosi print("---") între ele, ca în exemplul de mai devreme)

Bonus (opțional, dacă vrei provocare): încearcă să faci system prompt-ul să oblige modelul să răspundă doar în română, chiar dacă tu scrii accidental un mesaj în engleză."""

from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(system_instruction="Ești un asistent care ajută un operator de call center. "
                                       "Răspunde scurt, concis, în maxim 3 propoziții"
                                       "Răspunde întotdeauna în limba română, indiferent de limba în care este formulată întrebarea."),
)

response1 = chat.send_message("Sunt un client fidel al dumneavoastra, insa dupa ultima comanda am ramas stupefiat. " \
"Comanda a ajuns incompleta si coletul ud")
print("Model:", response1.text)
print("---")

response2 = chat.send_message("Ce as putea raspunde legat de situatia anterioara?")
print("Model:", response2.text)
print("---")

response3 = chat.send_message("Please offer me a more formal answer")
print("Model:", response3.text)
print("---")