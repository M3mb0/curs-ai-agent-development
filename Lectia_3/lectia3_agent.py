"""Instalează pypdf: pip install pypdf
Găsește un PDF simplu (poate chiar un document de la muncă, sau descarcă orice PDF scurt — manual, articol) și pune-l în Lectia_3/
Scrie un script care:
Extrage tot textul din PDF cu pypdf
Aplică funcția de chunking (poți folosi exemplul de mai sus sau să-ți scrii propria variantă)
Printează câte chunk-uri a rezultat și primele 200 caractere din primele 2-3 chunk-uri, ca verificare vizuală"""

from pypdf import PdfReader
import re
import tiktoken

reader = PdfReader("Lectia_3/Cristian_Ungureanu_TechSupport_CV.pdf")
text_complet = ""
for pagina in reader.pages:
    text_complet += pagina.extract_text()



def curata_text(text: str) -> str:
    """Curăță textul de spații/linii goale în exces."""
    text = re.sub(r'\n{3,}', '\n\n', text)      # max 2 linii goale consecutive
    text = re.sub(r' {2,}', ' ', text)           # max 1 spațiu între cuvinte
    text = text.strip()                           # elimină spații de la început/final
    return text

encoder = tiktoken.get_encoding("cl100k_base")  # encoder generic, folosit pe scară largă

def numara_tokeni(text: str) -> int:
    """Numără câți tokeni are un text."""
    return len(encoder.encode(text))

def imparte_cu_overlap(text: str, dimensiune: int, overlap: int, sursa: str) -> list:
    """Împarte textul în bucăți cu suprapunere, fiecare cu metadata atașată."""
    chunks = []
    index_chunk = 0
    for i in range(0, len(text), dimensiune - overlap):
        end = i + dimensiune
        bucata_text = text[i:end]

        chunk = {
            "text": bucata_text,
            "sursa": sursa,
            "index_chunk": index_chunk,
            "nr_tokeni":numara_tokeni(bucata_text)

        }
        chunks.append(chunk)
        index_chunk += 1
    return chunks


# Aplicăm chunking pe textul extras din CV
text_curatat = curata_text(text_complet)
chunks = imparte_cu_overlap(text_curatat, dimensiune=500, overlap=50, sursa="Cristian_Ungureanu_TechSupport_CV.pdf")


print(f"\nNumăr total de chunk-uri: {len(chunks)}\n")

for chunk in chunks[:3]:
    print(chunk)
    print()

# print(f" Numarul de tokeni este {numara_tokeni(text_curatat)}")
# print(f"Numarul de caratere este {len(text_curatat)}")