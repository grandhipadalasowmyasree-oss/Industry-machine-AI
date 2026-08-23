import re
import os
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai


# ============================================
# ENVIRONMENT
# ============================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found!")


# ============================================
# GEMINI
# ============================================

client = genai.Client(
    api_key=GEMINI_API_KEY,
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

    print(
        "QUESTION RECEIVED:",
        question
    )

    machine_id = find_machine_id(question)

    print(
        "DETECTED MACHINE ID:",
        machine_id
    )

    if machine_id:

        machine = get_machine_from_csv(
            machine_id
        )

        print(
            "MACHINE RESULT:",
            machine is not None
        )

        if machine is not None:

            machine_text = machine_to_text(
                machine
            )

            print(
                "MACHINE DATA FOUND!"
            )

            print(machine_text)

            sources = [{
                "source": "train.csv",
                "machine_id": machine_id
            }]

            return [machine_text], sources

        else:

            print(
                f"Machine {machine_id} "
                "was not found."
            )

            return [], []

    print(
        "NO MACHINE ID DETECTED."
    )

    return [], []


# ============================================
# GENERATE ANSWER
# ============================================

def generate_answer(
    question,
    documents,
    sources
):

    # ----------------------------------------
    # NO MACHINE DATA
    # ----------------------------------------

    if not documents:

        return (
            "I could not find the requested "
            "machine information."
        )

    # ----------------------------------------
    # CREATE CONTEXT
    # ----------------------------------------

    context = "\n\n".join(
        documents
    )

    # ----------------------------------------
    # PROMPT
    # ----------------------------------------

    prompt = f"""
You are an AI Industrial Safety and
Maintenance Assistant.

Answer the user's question using ONLY
the provided machine data.

IMPORTANT RULES:

1. Do not invent sensor values.
2. Do not change machine values.
3. Pay attention to the Machine ID.
4. Give a direct answer first.
5. Mention the important sensor values.
6. Explain the likely reason using only
   the available machine data.
7. Keep the answer simple and clear.
8. Use bullet points when useful.

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

For vibration questions, analyze:

- Vibration
- RPM
- Load
- Operating hours
- Days since maintenance
- Machine type
- Maintenance strategy

For maintenance questions, analyze:

- Maintenance strategy
- Days since maintenance
- Operating hours
- Vibration
- Temperature
- Oil pressure
- Anomaly count

MACHINE DATA:

{context}

USER QUESTION:

{question}
"""

    # ========================================
    # GEMINI MODELS
    # ========================================

    models_to_try = [

        "gemini-3.7-flash",

        "gemini-3.6-flash",

        "gemini-3.5-flash"

    ]

    # ========================================
    # TRY MODELS
    # ========================================

    for model_name in models_to_try:

        print(
            f"\nTrying Gemini model: "
            f"{model_name}"
        )

        # ------------------------------------
        # RETRY SAME MODEL
        # ------------------------------------

        for attempt in range(2):

            try:

                response = client.models.generate_content(

                    model=model_name,

                    contents=prompt

                )

                # --------------------------------
                # CHECK RESPONSE
                # --------------------------------

                if response and response.text:

                    print(
                        "\nGEMINI ANSWER GENERATED!"
                    )

                    print(
                        "MODEL USED:",
                        model_name
                    )

                    return response.text

                print(
                    "Empty response from model."
                )

            except Exception as e:

                error_message = str(e)

                print(
                    "\nGEMINI ERROR:"
                )

                print(
                    error_message
                )

                # =================================
                # RATE LIMIT 429
                # =================================

                if "429" in error_message:

                    print(
                        "Gemini quota/rate limit "
                        "reached."
                    )

                    if attempt == 0:

                        print(
                            "Waiting 5 seconds "
                            "before retry..."
                        )

                        time.sleep(5)

                        continue

                    else:

                        print(
                            "Trying next model..."
                        )

                        break

                # =================================
                # SERVICE UNAVAILABLE 503
                # =================================

                elif "503" in error_message:

                    print(
                        "Gemini service temporarily "
                        "unavailable."
                    )

                    if attempt == 0:

                        print(
                            "Waiting 5 seconds "
                            "before retry..."
                        )

                        time.sleep(5)

                        continue

                    else:

                        print(
                            "Trying next model..."
                        )

                        break

                # =================================
                # OTHER ERROR
                # =================================

                else:

                    print(
                        "Unexpected Gemini error."
                    )

                    break

    # ========================================
    # ALL MODELS FAILED
    # ========================================

    return (
        "I found the machine information, "
        "but the AI service is temporarily "
        "unavailable. Please try again in "
        "a few seconds."
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