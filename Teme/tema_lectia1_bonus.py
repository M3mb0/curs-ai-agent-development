"""Cerință: Mini-agent BPO cu 2 tool-uri

Construiește un script tema_lectia1_bonus.py (îl pui în folderul Teme/) care combină tot ce ai învățat: chat cu memorie + buclă interactivă + tool calling, dar de data asta cu două funcții, nu una.

1. Definește două funcții Python, relevante pentru BPO:

calculeaza_timp_asteptare(nr_apeluri_coada: int, nr_operatori: int) -> float
— calculează timp estimat de așteptare (poți simplifica: ex. nr_apeluri_coada / nr_operatori * 2 minute, sau orice formulă simplă, logică ta)
verifica_status_client(id_client: int) -> str
— simulează o verificare (nu trebuie bază de date reală!) — poate întoarce ceva fix, ex: f"Clientul {id_client} are status: activ, fără restanțe" (hardcodat, doar ca să testezi conceptul)

2. Creează un chat cu system prompt relevant (asistent BPO) și ambele funcții în tools=[...]

3. Folosește bucla interactivă (while True + input), ca modelul să poată decide, live, pe baza întrebărilor tale, care funcție să apeleze (sau dacă să apeleze vreuna)

Testează cu întrebări de genul:

"Avem 15 apeluri în coadă și 3 operatori activi, cât ar trebui să aștepte clienții?"
"Poți verifica statusul clientului cu ID 4521?"
"Ce părere ai despre cum decurge ziua?" (fără legătură cu niciun tool — testezi dacă modelul răspunde normal, fără să forțeze un apel de funcție)"""

from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#Definim prima functie Python
def calculeaza_timp_asteptare(nr_apeluri_coada: int, nr_operatori: int) -> str:
    """Calculează timpul estimat de așteptare pentru clienți în coadă.

    Args:
        nr_apeluri_coada: numărul de apeluri aflate în coadă
        nr_operatori: numărul de operatori activi disponibili
    """
    try:
        if nr_apeluri_coada < 0 or nr_operatori < 0:
            return "Eroare: valorile nu pot fi negative."
        
        timp = (nr_apeluri_coada / nr_operatori) * 2
        return f"Timp estimat de așteptare: {timp:.1f} minute"
    
    except ZeroDivisionError:
        return "Eroare: nu există operatori activi disponibili momentan."
    except Exception as e:
        return f"A apărut o eroare neașteptată: {str(e)}"

#Definim a doua functie Python
def verifica_status_client(id_client:int) -> str:
    """Verifica statusul clientului(Activ sau Inchis, cu sau fara restante) in baza unui ID
    
    Args:
        id_client: ID-ul clientului de forma int
    """
    return f"Clientul {id_client} are status: Activ fara restante"



# Creăm chat-ul, dar de data asta îi spunem ce tool-uri are la dispoziție
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(system_instruction="Ești un asistent care ajută la calcularea timpilor de asteptare."
                                                          "Verifica statusul unui client in baza unui ID."
                                                          "Raspunde tot timpul in limba romana"
                                                          "Exemple de răspunsuri dorite:"
                                                          "Întrebare: Cât aștept cu 20 apeluri și 5 operatori?"
                                                          "Răspuns bun: Timp estimat: 8 minute. Recomand alocarea unui operator suplimentar dacă durata depășește 10 minute."
                                                          "Întrebare: Clientul 1234 e ok?" 
                                                          "Răspuns bun: Da, clientul 1234 are status activ, fără restanțe. Poate fi procesat normal." 
                                                          "Urmează exact acest stil: concis, cu o concluzie/recomandare scurtă la final, ton profesional.",
                                       tools=[calculeaza_timp_asteptare, verifica_status_client], #aici ii dam acces la functie
                                       ),
)

print("Chat pornit! Scrie 'exit' ca să ieși.\n")

while True:
    user_input= input("Tu: ")
    if user_input.lower() == "exit":
            print("La revedere")
            break
    
    response = chat.send_message(user_input)
    print("Model:", response.text)
    print()