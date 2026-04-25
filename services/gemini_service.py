import os
import json
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.0-flash"


def analyze_medicine_image(image_path: str) -> str:
    """Extract medicine name from an uploaded image."""
    image = Image.open(image_path)

    prompt = (
        "Look at this medicine packaging. "
        "Extract ONLY the medicine brand name or generic name. "
        "Return only the name, nothing else. "
        "If you cannot identify any medicine, return 'NOT_FOUND'."
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=[prompt, image]
    )

    name = response.text.strip()
    if name == "NOT_FOUND" or not name:
        raise ValueError("Could not identify medicine from image.")
    return name


def get_medicine_info(medicine_name: str) -> dict:
    """Get complete bilingual medicine information."""
    prompt = f"""
You are DawaSaathi, a bilingual medical information assistant for Pakistan.
Provide complete information about the medicine: {medicine_name}

Return ONLY a valid JSON object with this exact structure (no markdown, no backticks):
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

Write Urdu in proper Nastaliq script. Be accurate and simple to understand.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    raw = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)


def get_medicine_from_symptoms(symptoms: str, age: str, severity: str) -> dict:
    """Suggest medicine based on symptoms, age, and severity."""
    severity_note = ""
    if severity.lower() in ["severe", "high", "بہت زیادہ"]:
        severity_note = (
            "The symptoms are SEVERE. "
            "Strongly recommend seeing a doctor immediately. "
            "But also suggest ONE safe OTC medicine to ease the pain temporarily."
        )

    prompt = f"""
You are DawaSaathi, a bilingual AI medical assistant for Pakistan.

A user has the following situation:
- Symptoms/Pain: {symptoms}
- Age: {age}
- Severity: {severity}
{severity_note}

Suggest the most appropriate and safe over-the-counter medicine.

Return ONLY a valid JSON object (no markdown, no backticks):
{{
  "suggested_medicine": "...",
  "urdu_name": "...",
  "reason": {{
    "en": "Why this medicine is suggested",
    "ur": "یہ دوا کیوں تجویز کی گئی"
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
    "en": "This is not a substitute for professional medical advice.",
    "ur": "یہ پیشہ ور طبی مشورے کا متبادل نہیں ہے۔"
  }}
}}

Write Urdu in proper Nastaliq script.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    raw = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)