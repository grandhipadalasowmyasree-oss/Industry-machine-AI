import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

# ==============================
# 1. LOAD MACHINE DATA
# ==============================

df = pd.read_csv("train.csv")

print("Dataset loaded!")
print("Rows:", len(df))
print("Columns:", len(df.columns))

# ==============================
# 2. CREATE MACHINE DOCUMENTS
# ==============================

documents = []
metadatas = []
ids = []

for index, row in df.iterrows():

    machine_text = f"""
Machine ID: {row['id']}
Machine Type: {row['machine_type']}
Facility Zone: {row['facility_zone']}
Shift: {row['shift']}
Sensor Model: {row['sensor_model']}
Maintenance Strategy: {row['maintenance_strategy']}

Load: {row['load_pct']} %
RPM: {row['rpm']}
Power: {row['power_kw']} kW
Voltage: {row['voltage_v']} V
Power Factor: {row['power_factor']}
Vibration: {row['vibration_mm_s']} mm/s
Oil Pressure: {row['oil_pressure_bar']} bar
Coolant Temperature: {row['coolant_temp_c']} C
Bearing Temperature: {row['bearing_temp_c']} C

Operating Hours: {row['operating_hours']}
Days Since Maintenance: {row['days_since_maintenance']}
Anomaly Count (7d): {row['anomaly_count_7d']}
Sensor Uptime: {row['sensor_uptime_pct']} %
Machine State: {row['machine_state']}
"""

    documents.append(machine_text)

    metadatas.append({
        "machine_id": str(row["id"]),
        "machine_type": str(row["machine_type"]),
        "source": "train.csv"
    })

    ids.append(str(row["id"]))


# ==============================
# 3. CREATE EMBEDDINGS
# ==============================

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

embeddings = model.encode(documents)

print("Embeddings created!")


# ==============================
# 4. CHROMADB
# ==============================

client = chromadb.PersistentClient(
    path="chroma_db"
)

# Delete old collection
try:
    client.delete_collection(
        name="industrial_knowledge"
    )
    print("Old collection deleted.")
except:
    pass

collection = client.create_collection(
    name="industrial_knowledge"
)


# ==============================
# 5. STORE DATA
# ==============================

collection.add(
    ids=ids,
    embeddings=embeddings.tolist(),
    documents=documents,
    metadatas=metadatas
)

print("Machine data stored successfully!")
print("Total machines:", collection.count())