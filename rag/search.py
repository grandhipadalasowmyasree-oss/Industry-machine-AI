import chromadb
from sentence_transformers import SentenceTransformer

# Load ChromaDB
client = chromadb.PersistentClient(
    path="../chroma_db"
)

collection = client.get_collection(
    name="industrial_knowledge"
)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Ask a question
query = input("\nAsk your question: ")

# Convert question into embedding
query_embedding = model.encode([query])[0]

# Search ChromaDB
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=3
)

print("\n🔎 Retrieved Information:\n")

for i in range(len(results["documents"][0])):
    print(f"--- Result {i + 1} ---")
    print("Source:", results["metadatas"][0][i]["source"])
    print(results["documents"][0][i])
    print()