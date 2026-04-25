import os
import json
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.0-flash"


# =========================
# IMAGE ANALYSIS FUNCTION
# =========================
def analyze_medicine_image(image_path: str) -> str:
    """Extract medicine name from an uploaded image."""

    image = Image.open(image_path)

    prompt = (
        "Look at this medicine packaging. "
        "Extract ONLY the medicine brand name or generic name. "
        "Return only the name. "
        "If you cannot identify it, return NOT_FOUND."
    )

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content([prompt, image])

    name = response.text.strip()

    if not name or name == "NOT_FOUND":
        raise ValueError("Could not identify medicine from image.")

    return name


# =========================
# MEDICINE INFO FUNCTION
# =========================
def get_medicine_info(medicine_name: str) -> dict:
    """Get complete bilingual medicine information."""

    prompt = f"""
You are DawaSaathi, a bilingual medical assistant for Pakistan.

Provide complete information about: {medicine_name}

Return ONLY valid JSON (no markdown):

{{
  "medicine_name": "...",
  "urdu_name": "...",
  "active_ingredient": {{
    "en": "...",
    "ur": "..."
  }},
  "uses": {{
    "en": "...",
    "ur": "..."
  }},
  "how_to_take": {{
    "en": "...",
    "ur": "..."
  }},
  "dosage": {{
    "en": "...",
    "ur": "..."
  }},
  "side_effects": {{
    "en": "...",
    "ur": "..."
  }},
  "warnings": {{
    "en": "...",
    "ur": "..."
  }},
  "alternatives": {{
    "en": "...",
    "ur": "..."
  }},
  "disclaimer": {{
    "en": "Always consult a doctor before taking any medicine.",
    "ur": "کوئی بھی دوا لینے سے پہلے ڈاکٹر سے مشورہ کریں۔"
  }}
}}

Write Urdu in proper Nastaliq style.
"""

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)

    raw = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)


# =========================
# SYMPTOM-BASED SUGGESTION
# =========================
def get_medicine_from_symptoms(symptoms: str, age: str, severity: str) -> dict:
    """Suggest medicine based on symptoms."""

    severity_note = ""
    if severity.lower() in ["severe", "high", "بہت زیادہ"]:
        severity_note = (
            "Symptoms are severe. Strongly recommend seeing a doctor immediately. "
            "Also suggest one safe OTC medicine for temporary relief."
        )

    prompt = f"""
You are DawaSaathi, a medical assistant for Pakistan.

User details:
- Symptoms: {symptoms}
- Age: {age}
- Severity: {severity}

{severity_note}

Return ONLY valid JSON:

{{
  "suggested_medicine": "...",
  "urdu_name": "...",
  "reason": {{
    "en": "...",
    "ur": "..."
  }},
  "uses": {{
    "en": "...",
    "ur": "..."
  }},
  "dosage": {{
    "en": "...",
    "ur": "..."
  }},
  "warnings": {{
    "en": "...",
    "ur": "..."
  }},
  "see_doctor": {{
    "recommended": true,
    "message": {{
      "en": "...",
      "ur": "..."
    }}
  }},
  "disclaimer": {{
    "en": "This is not a substitute for medical advice.",
    "ur": "یہ طبی مشورے کا متبادل نہیں ہے۔"
  }}
}}

Write Urdu in proper Nastaliq script.
"""

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)

    raw = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)