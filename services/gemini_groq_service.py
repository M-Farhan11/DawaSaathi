import os
import json
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not set in .env")

client = Groq(api_key=API_KEY)
MODEL = "llama-3.3-70b-versatile"


class GeminiAPIError(Exception):
    pass


def _parse_json(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def _chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def analyze_medicine_image(image_path: str) -> str:
    raise GeminiAPIError(
        "Image analysis is not available. Please type the medicine name or use voice input."
    )


def get_medicine_info(medicine_name: str) -> dict:
    if not medicine_name or not isinstance(medicine_name, str):
        raise GeminiAPIError("Medicine name is required")

    medicine_name = medicine_name.strip()[:100]

    prompt = f"""You are DawaSaathi, a bilingual medical assistant for Pakistan.
Provide information about: {medicine_name}

Return ONLY valid JSON, no markdown, no code blocks:

{{
  "medicine_name": "...",
  "urdu_name": "...",
  "active_ingredient": {{"en": "...", "ur": "..."}},
  "uses": {{"en": "...", "ur": "..."}},
  "how_to_take": {{"en": "...", "ur": "..."}},
  "dosage": {{"en": "...", "ur": "..."}},
  "side_effects": {{"en": "...", "ur": "..."}},
  "warnings": {{"en": "...", "ur": "..."}},
  "alternatives": {{"en": "...", "ur": "..."}},
  "disclaimer": {{
    "en": "Always consult a doctor before taking any medicine.",
    "ur": "کوئی بھی دوا لینے سے پہلے ڈاکٹر سے مشورہ کریں۔"
  }}
}}"""

    try:
        return _parse_json(_chat(prompt))
    except json.JSONDecodeError:
        raise GeminiAPIError("Failed to parse medicine information. Please try again.")
    except Exception as e:
        raise GeminiAPIError(f"Failed to fetch medicine info: {e}")


def get_medicine_from_symptoms(symptoms: str, age: str, severity: str) -> dict:
    if not symptoms:
        raise GeminiAPIError("Symptoms are required")

    symptoms = symptoms.strip()[:500]
    age = (age or "adult").strip()[:20]
    severity = (severity or "mild").strip()[:20]

    severity_note = ""
    if severity.lower() in ["severe", "high", "critical", "بہت زیادہ"]:
        severity_note = "Symptoms are SEVERE. Strongly recommend seeing a doctor immediately. Also suggest one safe OTC medicine for temporary relief."

    prompt = f"""You are DawaSaathi, a bilingual medical assistant for Pakistan.

Patient: Symptoms: {symptoms} | Age: {age} | Severity: {severity}
{severity_note}

Return ONLY valid JSON, no markdown, no code blocks:

{{
  "suggested_medicine": "...",
  "urdu_name": "...",
  "reason": {{"en": "...", "ur": "..."}},
  "uses": {{"en": "...", "ur": "..."}},
  "dosage": {{"en": "...", "ur": "..."}},
  "warnings": {{"en": "...", "ur": "..."}},
  "see_doctor": {{
    "recommended": true,
    "message": {{"en": "...", "ur": "..."}}
  }},
  "disclaimer": {{
    "en": "This is not a substitute for professional medical advice.",
    "ur": "یہ طبی مشورے کا متبادل نہیں ہے۔"
  }}
}}"""

    try:
        return _parse_json(_chat(prompt))
    except json.JSONDecodeError:
        raise GeminiAPIError("Failed to parse symptom suggestion. Please try again.")
    except Exception as e:
        raise GeminiAPIError(f"Failed to fetch symptom suggestion: {e}")


def sanitize_input(text: str, max_length: int = 255) -> str:
    if not isinstance(text, str):
        return ""
    return text.strip()[:max_length]