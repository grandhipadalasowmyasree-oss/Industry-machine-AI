import re
import os
import pandas as pd
import chromadb
from google import genai
from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# GEMINI
# =========================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("WARNING: GEMINI_API_KEY not found.")

client = genai.Client(
    api_key=api_key,
    http_options={"api_version": "v1"}
)


# =========================================================
# LOAD TRAIN DATA
# =========================================================

df = pd.read_csv("data/train.csv")

print("Machine dataset loaded!")
print("Total machines:", len(df))


# =========================================================
# CHROMADB
# =========================================================

try:

    chroma_client = chromadb.PersistentClient(
        path="chroma_db"
    )

    collection = chroma_client.get_collection(
        name="industrial_knowledge"
    )

    print(
        "Documents in ChromaDB:",
        collection.count()
    )

except Exception as e:

    print(
        "ChromaDB could not be loaded:",
        e
    )

    chroma_client = None
    collection = None


# =========================================================
# FIND MACHINE ID
# =========================================================

def find_machine_id(question):

    match = re.search(
        r"machine\s*(?:id\s*)?(\d+)",
        question.lower()
    )

    if match:

        return match.group(1)

    return None


# =========================================================
# GET MACHINE FROM CSV
# =========================================================

def get_machine_from_csv(machine_id):

    machine = df[
        df["id"].astype(str) == str(machine_id)
    ]

    if machine.empty:

        return None

    return machine.iloc[0]


# =========================================================
# CONVERT MACHINE DATA TO TEXT
# =========================================================

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


# =========================================================
# MACHINE SEARCH
# =========================================================

def search_machine(question):

    machine_id = find_machine_id(question)

    if not machine_id:

        return None, None

    print(
        f"\nSearching machine {machine_id}..."
    )

    machine = get_machine_from_csv(
        machine_id
    )

    if machine is None:

        print(
            f"Machine {machine_id} "
            "was not found in train.csv."
        )

        return None, machine_id

    machine_text = machine_to_text(
        machine
    )

    print(
        "\nMachine found successfully."
    )

    sources = [
        {
            "source": "train.csv",
            "machine_id": machine_id
        }
    ]

    return machine_text, sources


# =========================================================
# SIMPLE CHROMADB SEARCH
# =========================================================

def search_knowledge_base(question):

    if collection is None:

        print(
            "Knowledge base is not available."
        )

        return [], []

    try:

        # ChromaDB can use its configured embedding
        # function if the collection was created with one.

        results = collection.query(
            query_texts=[question],
            n_results=3
        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        sources = results.get(
            "metadatas",
            [[]]
        )[0]

        return documents, sources

    except Exception as e:

        print(
            "Knowledge base search error:",
            e
        )

        return [], []


# =========================================================
# RETRIEVE DOCUMENTS
# =========================================================

def retrieve_documents(question):

    # =====================================================
    # FIRST: CHECK MACHINE ID
    # =====================================================

    machine_text, machine_sources = search_machine(
        question
    )

    if machine_text:

        return [
            machine_text
        ], machine_sources


    # =====================================================
    # SECOND: SEARCH KNOWLEDGE BASE
    # =====================================================

    print(
        "\nSearching industrial "
        "safety knowledge base..."
    )

    documents, sources = search_knowledge_base(
        question
    )

    return documents, sources


# =========================================================
# GENERATE ANSWER
# =========================================================

def generate_answer(
    question,
    documents,
    sources
):

    if not documents:

        return (
            "I don't have enough information "
            "in the provided knowledge base."
        )


    # =====================================================
    # CREATE CONTEXT
    # =====================================================

    context = "\n\n".join(
        documents
    )


    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are an AI Industrial Safety and
Maintenance Assistant.

Your job is to answer questions about
industrial machines, safety and maintenance.

IMPORTANT RULES:

1. Use ONLY the information provided in
   the context.

2. Never invent sensor values.

3. If machine data is available,
   use the exact values.

4. Always pay attention to the Machine ID.

5. For machine-specific questions,
   give a machine-specific answer.

6. Do not invent information that is
   not present in the context.

7. Keep the answer simple and easy
   to understand.

8. If the context does not contain
   enough information, clearly say that
   the information is not available.


For overheating questions, consider:

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


CONTEXT:

{context}


USER QUESTION:

{question}


RESPONSE FORMAT:

Give the direct answer first.

Then mention the important sensor
values or information.

Then explain the possible reason
when the context supports it.

Use bullet points when useful.

Keep the response clear and concise.
"""


    # =====================================================
    # GEMINI MODELS
    # =====================================================

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash"
    ]


    # =====================================================
    # GENERATE RESPONSE
    # =====================================================

    for model_name in models_to_try:

        try:

            print(
                f"Generating answer using {model_name}..."
            )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if response and response.text:

                return response.text


        except Exception as e:

            print(
                f"Model {model_name} failed:"
            )

            print(e)

            continue


    # =====================================================
    # ALL MODELS FAILED
    # =====================================================

    return (
        "Sorry, I could not generate an answer "
        "at the moment. Please try again."
    )


# =========================================================
# TERMINAL CHAT
# =========================================================

if __name__ == "__main__":

    print(
        "\nAI Industrial Assistant"
    )

    print(
        "Type 'exit' to stop.\n"
    )


    while True:

        question = input(
            "You: "
        )


        if question.lower() == "exit":

            print(
                "Goodbye!"
            )

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

        print(
            answer
        )


        print(
            "\nSources:"
        )


        unique_sources = set()


        for source in sources:

            if not source:

                continue


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