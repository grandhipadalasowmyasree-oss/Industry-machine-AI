import os
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# -----------------------------
# 1. Load documents
# -----------------------------

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


# -----------------------------
# 2. Split documents
# -----------------------------

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


# -----------------------------
# 3. Create embeddings
# -----------------------------

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [chunk["text"] for chunk in chunks]

embeddings = model.encode(texts)

print("Embeddings created!")


# -----------------------------
# 4. Create ChromaDB
# -----------------------------

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_or_create_collection(
    name="industrial_knowledge"
)


# -----------------------------
# 5. Store chunks + embeddings
# -----------------------------

collection.add(
    ids=[str(i) for i in range(len(chunks))],
    embeddings=embeddings.tolist(),
    documents=texts,
    metadatas=[
        {"source": chunk["filename"]}
        for chunk in chunks
    ]
)

print("Documents stored in ChromaDB!")
print("Total documents:", collection.count())