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


def imparte_cu_overlap(text: str, dimensiune: int, overlap: int) -> list:
    """Împarte textul în bucăți cu suprapunere."""
    chunks = []
    for i in range(0, len(text), dimensiune - overlap):
        end = i + dimensiune
        chunks.append(text[i:end])
    return chunks


def numara_tokeni(text: str) -> int:
    """Numără câți tokeni are un text."""
    return len(encoder.encode(text))

# Aplicăm chunking pe textul extras din CV
text_curatat = curata_text(text_complet)
chunks = imparte_cu_overlap(text_curatat, dimensiune=500, overlap=50)

encoder = tiktoken.get_encoding("cl100k_base")  # encoder generic, folosit pe scară largă



print(f"\nNumăr total de chunk-uri: {len(chunks)}\n")

# for i, chunk in enumerate(chunks):
#     print(f"--- Chunk {i+1} ---")
#     print(chunk[:200])  # primele 200 caractere din fiecare chunk, ca verificare
#     print()

print(f" Numarul de tokeni este {numara_tokeni(text_curatat)}")
print(f"Numarul de caratere este {len(text_curatat)}")