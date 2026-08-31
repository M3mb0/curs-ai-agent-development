from pathlib import Path

def load_documents_from_folder(folder_path: str) -> list:
    """Loads all .md files from a folder as a list of documents.

    Args:
        folder_path: path to the folder containing .md files

    Returns:
        A list of dicts, each with "filename" and "text" keys.
    """
    folder = Path(folder_path) #creezi obiectul Path din folder_path
    result = [] #creezi o listă goală
    for f in folder.glob("*.md"): #faci o buclă for, prin folder.glob("*.md")
         doc = {"filename": f.name, "text": f.read_text(encoding="utf-8")}  #la fiecare pas, ai un "file" - construiești un dicționar cu file.name și file.read_text(...)
         result.append(doc)  #adaugi acel dicționar în listă
   
    return result #returnezi lista


if __name__ == "__main__":
    docs = load_documents_from_folder("wfm-agent-project/data/kb_documents")
    print(f"Am încărcat {len(docs)} documente")
    print(docs[0]["filename"])
    print(docs[0]["text"][:200])