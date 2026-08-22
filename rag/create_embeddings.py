import os
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

KNOWLEDGE_BASE = "../knowledge_base"

# Load documents
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

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = []

for document in documents:
    document_chunks = text_splitter.split_text(document["text"])

    for chunk in document_chunks:
        chunks.append({
            "filename": document["filename"],
            "text": chunk
        })

print("Total chunks:", len(chunks))

# Load embedding model
print("\nLoading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded!")

# Create embeddings
texts = [chunk["text"] for chunk in chunks]

embeddings = model.encode(texts)

print("\nEmbeddings created!")
print("Number of embeddings:", len(embeddings))
print("Embedding dimensions:", embeddings.shape[1])

# Show first embedding
print("\nFirst embedding:")
print(embeddings[0])