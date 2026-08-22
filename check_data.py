import chromadb

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_collection(
    name="industrial_knowledge"
)

print("Total records:", collection.count())

result = collection.get(
    where={
        "machine_id": "19325"
    }
)

print("\nRecords found:", len(result["documents"]))

for doc in result["documents"]:
    print("\n====================")
    print(doc)