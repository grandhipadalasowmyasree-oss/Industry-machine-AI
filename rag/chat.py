import re
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"api_version": "v1"}
)
import pandas as pd
from google import genai
from dotenv import load_dotenv

# ============================================
# ENVIRONMENT
# ============================================

load_dotenv()

# ============================================
# GEMINI
# ============================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"api_version": "v1"}
)

# ============================================
# LOAD DATASET
# ============================================

df = pd.read_csv("data/train.csv")

print("Machine dataset loaded!")
print("Total machines:", len(df))


# ============================================
# FIND MACHINE ID
# ============================================

def find_machine_id(question):

    match = re.search(
        r"machine\s*(?:id\s*)?(\d+)",
        question.lower()
    )

    if match:
        return match.group(1)

    return None


# ============================================
# GET MACHINE FROM CSV
# ============================================

def get_machine_from_csv(machine_id):

    try:
        machine_id = int(machine_id)

        machine = df[
            pd.to_numeric(
                df["id"],
                errors="coerce"
            ) == machine_id
        ]

        if machine.empty:
            print(
                f"Machine {machine_id} not found."
            )
            return None

        print(
            f"Machine {machine_id} found!"
        )

        return machine.iloc[0]

    except Exception as e:

        print(
            "DATASET SEARCH ERROR:",
            e
        )

        return None


# ============================================
# MACHINE DATA → TEXT
# ============================================

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


# ============================================
# RETRIEVE DOCUMENTS
# ============================================
def retrieve_documents(question):

    print("QUESTION RECEIVED:", question)

    machine_id = find_machine_id(question)

    print("DETECTED MACHINE ID:", machine_id)

    if machine_id:

        machine = get_machine_from_csv(machine_id)

        print("MACHINE RESULT:", machine is not None)

        if machine is not None:

            machine_text = machine_to_text(machine)

            print("MACHINE DATA FOUND!")
            print(machine_text)

            sources = [{
                "source": "train.csv",
                "machine_id": machine_id
            }]

            return [machine_text], sources

        else:

            print(
                f"Machine {machine_id} was not found."
            )

            return [], []

    print("NO MACHINE ID DETECTED.")

    return [], []

# ============================================
# GENERATE ANSWER
# ============================================

def generate_answer(
    question,
    documents,
    sources
):

    if not documents:

        return (
            "I could not find the requested "
            "machine information."
        )

    context = "\n\n".join(documents)

    prompt = f"""
You are an AI Industrial Safety and
Maintenance Assistant.

Answer the user's question using ONLY
the provided machine data.

Do not invent any sensor values.

Machine data:

{context}

User question:

{question}

Instructions:

1. Give the direct answer first.
2. Mention the important sensor values.
3. For overheating questions, analyze:
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

4. For maintenance questions, analyze:
   - Maintenance strategy
   - Days since maintenance
   - Operating hours
   - Vibration
   - Temperature
   - Oil pressure

5. Keep the answer simple and clear.
6. Use bullet points when useful.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print(
            "GEMINI ERROR:",
            e
        )

        return (
            "Sorry, I could not generate "
            "an answer at the moment. "
            "Please try again."
        )


# ============================================
# TERMINAL TEST
# ============================================

if __name__ == "__main__":

    print(
        "\nAI Industrial Assistant"
    )

    print(
        "Type exit to stop.\n"
    )

    while True:

        question = input("You: ")

        if question.lower() == "exit":

            break

        documents, sources = retrieve_documents(
            question
        )

        answer = generate_answer(
            question,
            documents,
            sources
        )

        print("\nAssistant:")
        print(answer)