import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

KNOWLEDGE_BASE = "../knowledge_base"

documents = []

# Load documents
for filename in os.listdir(KNOWLEDGE_BASE):
    if filename.endswith(".txt"):
        filepath = os.path.join(KNOWLEDGE_BASE, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()

        documents.append({
            "filename": filename,
            "text": text
        })

# Create text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

all_chunks = []

# Split documents
for document in documents:
    chunks = text_splitter.split_text(document["text"])

    for chunk in chunks:
        all_chunks.append({
            "filename": document["filename"],
            "text": chunk
        })

print("Total chunks:", len(all_chunks))

for i, chunk in enumerate(all_chunks[:5]):
    print("\n--- Chunk", i + 1, "---")
    print("Source:", chunk["filename"])
    print(chunk["text"])