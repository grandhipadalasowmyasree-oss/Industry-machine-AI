import re
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from dotenv import load_dotenv

# ==============================
# LOAD ENVIRONMENT VARIABLES
# ==============================

load_dotenv()


# ==============================
# GEMINI
# ==============================

client = genai.Client(
    http_options={"api_version": "v1"}
)


# ==============================
# LOAD TRAIN DATA
# ==============================

df = pd.read_csv("data/train.csv")

print("Machine dataset loaded!")
print("Total machines:", len(df))


# ==============================
# CHROMADB
# ==============================

chroma_client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = chroma_client.get_collection(
    name="industrial_knowledge"
)

print("Documents in ChromaDB:", collection.count())


# ==============================
# EMBEDDING MODEL
# ==============================

# IMPORTANT:
# Do NOT load SentenceTransformer during startup.
# It will be loaded only when normal RAG search is needed.

embedding_model = None


def get_embedding_model():

    global embedding_model

    if embedding_model is None:

        print("Loading embedding model...")

        embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )

        print("Embedding model loaded!")

    return embedding_model


# ==============================
# FIND MACHINE ID
# ==============================

def find_machine_id(question):

    match = re.search(
        r"machine\s*(?:id\s*)?(\d+)",
        question.lower()
    )

    if match:
        return match.group(1)

    return None


# ==============================
# GET MACHINE FROM CSV
# ==============================

def get_machine_from_csv(machine_id):

    machine = df[
        df["id"].astype(str) == str(machine_id)
    ]

    if machine.empty:
        return None

    return machine.iloc[0]


# ==============================
# CONVERT MACHINE TO TEXT
# ==============================

def machine_to_text(machine):

    return f"""
Machine ID: {machine['id']}
Machine Type: {machine['machine_type']}
Facility Zone: {machine['facility_zone']}
Shift: {machine['shift']}
Sensor Model: {machine['sensor_model']}
Maintenance Strategy: {machine['maintenance_strategy']}

Load: {machine['load_pct']} %
RPM: {machine['rpm']}
Power: {machine['power_kw']} kW
Voltage: {machine['voltage_v']} V
Power Factor: {machine['power_factor']}
Vibration: {machine['vibration_mm_s']} mm/s
Oil Pressure: {machine['oil_pressure_bar']} bar
Coolant Temperature: {machine['coolant_temp_c']} °C
Bearing Temperature: {machine['bearing_temp_c']} °C

Operating Hours: {machine['operating_hours']}
Days Since Maintenance: {machine['days_since_maintenance']}
Anomaly Count (7d): {machine['anomaly_count_7d']}
Sensor Uptime: {machine['sensor_uptime_pct']} %
Machine State: {machine['machine_state']}
"""


# ==============================
# RETRIEVE DOCUMENTS
# ==============================

def retrieve_documents(question):

    # --------------------------------
    # Check for machine ID FIRST
    # --------------------------------

    machine_id = find_machine_id(question)

    if machine_id:

        print(
            f"\nSearching machine {machine_id}..."
        )

        machine = get_machine_from_csv(
            machine_id
        )

        if machine is not None:

            machine_text = machine_to_text(
                machine
            )

            sources = [{
                "source": "train.csv",
                "machine_id": machine_id
            }]

            return [machine_text], sources

        print(
            f"Machine {machine_id} "
            "was not found in train.csv."
        )

    # --------------------------------
    # Normal RAG search
    # --------------------------------

    print(
        "\nSearching the machine "
        "health knowledge base..."
    )

    # Load embedding model ONLY now
    model = get_embedding_model()

    question_embedding = model.encode(
        [question],
        convert_to_numpy=True
    )[0]

    results = collection.query(
        query_embeddings=[
            question_embedding.tolist()
        ],
        n_results=3
    )

    documents = results["documents"][0]

    sources = results["metadatas"][0]

    return documents, sources


# ==============================
# GENERATE ANSWER
# ==============================

def generate_answer(
    question,
    documents,
    sources
):

    if not documents:

        return (
            "I don't have enough information "
            "in the provided documents."
        )

    context = "\n\n".join(
        documents
    )

    prompt = f"""
You are an AI Industrial Safety and
Maintenance Assistant.

You must answer the user's question
using the provided machine data.

IMPORTANT RULES:

1. Use ONLY the provided machine data.
2. Never invent sensor values.
3. If the requested value exists in the
   machine data, give the exact value.
4. Pay attention to the Machine ID.
5. Give machine-specific answers.
6. Do not give generic answers when
   machine data is available.

For overheating questions, analyze:

- Load
- RPM
- Power
- Vibration
- Oil pressure
- Coolant temperature
- Bearing temperature
- Operating hours
- Days since maintenance
- Anomaly count

For maintenance questions, consider:

- Days since maintenance
- Operating hours
- Maintenance strategy
- Vibration
- Temperature
- Oil pressure

MACHINE DATA:

{context}

USER QUESTION:

{question}

RESPONSE RULES:

- Give a direct answer first.
- Mention the relevant sensor values.
- Explain the reason when appropriate.
- Use headings when useful.
- Use bullet points for recommendations.
- Keep the answer simple and clear.
"""

    models_to_try = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash"
    ]

    for model_name in models_to_try:

        try:

            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Model {model_name} unavailable."
            )

            print(e)

            continue

    return (
        "Sorry, all available AI models "
        "are temporarily unavailable."
    )


# ==============================
# TERMINAL CHAT
# ==============================

if __name__ == "__main__":

    print(
        "\nAI Industrial Assistant"
    )

    print(
        "Type 'exit' to stop.\n"
    )

    while True:

        question = input("You: ")

        if question.lower() == "exit":

            print("Goodbye!")

            break

        documents, sources = retrieve_documents(
            question
        )

        answer = generate_answer(
            question,
            documents,
            sources
        )

        print(
            "\nAssistant:"
        )

        print(answer)

        print(
            "\nSources:"
        )

        unique_sources = set()

        for source in sources:

            source_name = source.get(
                "source",
                "Unknown"
            )

            if source_name not in unique_sources:

                print(
                    "-",
                    source_name
                )

                unique_sources.add(
                    source_name
                )

        print()