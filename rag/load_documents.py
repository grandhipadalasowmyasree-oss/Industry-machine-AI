import os

KNOWLEDGE_BASE = "knowledge_base"

documents = []

for filename in os.listdir(KNOWLEDGE_BASE):
    if filename.endswith(".txt"):
        filepath = os.path.join(KNOWLEDGE_BASE, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()

        documents.append({
            "filename": filename,
            "text": text
        })

print("Documents loaded:", len(documents))

for document in documents:
    print("\nFile:", document["filename"])
    print("Characters:", len(document["text"]))