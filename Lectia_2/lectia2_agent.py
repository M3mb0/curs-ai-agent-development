from google import genai
from google.genai import types
from dotenv import load_dotenv
from langsmith import traceable
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

#Definim a treia functie Python
def estimeaza_prioritate_client(nr_comenzi_anterioare: int, valoare_totala_comenzi: float) -> str:
    """Verifica tipul clientului VIP sau standard in baza comenzilor emise si a valorii acestora
    
    Args:
        nr_comenzi_anterioare = numarul de comenzi emise de client
        valoare_totala_comenzi - valoarea totala a comenzilor emise de catre client
    """
    try:
        medie_comanda = valoare_totala_comenzi/nr_comenzi_anterioare
        if medie_comanda > 1000 and nr_comenzi_anterioare > 10:
            return "Client VIP"
        return "Client Standard"

    except ZeroDivisionError:
        return"Eroare: Daca valoarea totala a comenzilor este 0, atunci clienul nu a emis comenzi pana in acest moment"


#Inregistram aceste funcții în LangSmith pentru tracing
@traceable
def trimite_mesaj(chat, mesaj: str):
    return chat.send_message(mesaj)

# Creăm chat-ul, dar de data asta îi spunem ce tool-uri are la dispoziție
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(system_instruction="""Ești un asistent care ajută operatorii de call center BPO.
Ai acces la tool-uri pentru calcularea timpilor de așteptare, verificarea statusului clienților si tipul clientului pentru prioritizare.
Răspunde tot timpul în limba română.

Exemple de răspunsuri dorite:

Întrebare: "Cât aștept cu 20 apeluri și 5 operatori?"
Răspuns bun: "Timp estimat: 8 minute. Recomand alocarea unui operator suplimentar dacă durata depășește 10 minute."

Întrebare: "Clientul 1234 e ok?"
Răspuns bun: "Da, clientul 1234 are status activ, fără restanțe. Poate fi procesat normal."

Întrebare: "Daca un client a emis 10 comenzi in valoare toatala de 15000 de lei, ce tip de client este considerat?"
Raspuns bun: "In baza comenzilor emise si a valori lor(1500 lei/comanda), acesta este un client VIP iar timpul de asteptare va fi redus cu pana la 30%"

Urmează exact acest stil: concis, cu o concluzie sau recomandare scurtă la final, ton profesional.""",
                                       tools=[calculeaza_timp_asteptare, verifica_status_client, estimeaza_prioritate_client], #aici ii dam acces la functii
                                       ),
)

print("Chat pornit! Scrie 'exit' ca să ieși.\n")

while True:
    user_input= input("Tu: ")
    if user_input.lower() == "exit":
            print("La revedere")
            break
    
    response = trimite_mesaj(chat, user_input)
    print("Model:", response.text)
    print()