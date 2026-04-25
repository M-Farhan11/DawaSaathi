import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from services.gemini_groq_service import (
    analyze_medicine_image,
    get_medicine_info,
    get_medicine_from_symptoms,
    GeminiAPIError,
    sanitize_input,
)

load_dotenv()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


HEALTH_ISSUES = {
    "headache": {
        "name_en": "Headache", "name_ur": "سر درد", "icon": "psychology",
        "intro_en": "Headaches are common but can be disruptive. Most are harmless and can be managed with rest or basic care.",
        "intro_ur": "سر درد ایک عام مسئلہ ہے جو آرام یا عام احتیاط سے ٹھیک ہو سکتا ہے۔",
        "causes": [
            {"icon": "air", "color": "tertiary", "name_en": "Stress", "name_ur": "ذہنی دباؤ"},
            {"icon": "water_drop", "color": "secondary", "name_en": "Dehydration", "name_ur": "پانی کی کمی"},
            {"icon": "dark_mode", "color": "primary", "name_en": "Lack of Sleep", "name_ur": "نیند کی کمی"},
            {"icon": "visibility", "color": "secondary", "name_en": "Eye Strain", "name_ur": "نظر کی تھکاوٹ"}
        ],
        "remedies": [
            {"icon": "bed", "name_en": "Rest in Dark Room", "name_ur": "اندھیرے کمرے میں آرام"},
            {"icon": "local_drink", "name_en": "Drink Water", "name_ur": "زیادہ پانی پئیں"},
            {"icon": "self_care", "name_en": "Gentle Massage", "name_ur": "ہلکا مساج کریں"}
        ],
        "medicines": [
            {"name": "Panadol", "generic": "Paracetamol", "timing": "Every 4-6 hours", "dosage": "Max 8 tablets/day", "urdu_note": "کھانے کے بعد 1-2 گولیاں لیں۔"},
            {"name": "Brufen", "generic": "Ibuprofen", "timing": "After meals only", "dosage": "Avoid if stomach sensitive", "urdu_note": "ہمیشہ کھانے کے بعد لیں۔"}
        ],
        "red_flags": [
            {"en": "Sudden, severe thunderclap pain", "ur": "اچانک اور ناقابل برداشت درد"},
            {"en": "With high fever or stiff neck", "ur": "تیز بخار یا گردن کا اکڑ جانا"},
            {"en": "Blurred vision or confusion", "ur": "نظر کی دھندلاہٹ"}
        ]
    },
    "fever": {
        "name_en": "Fever", "name_ur": "بخار", "icon": "thermometer",
        "intro_en": "Fever is the body's natural response to infection. Most fevers can be managed at home.",
        "intro_ur": "بخار جسم کا انفیکشن کے خلاف فطری ردعمل ہے۔",
        "causes": [
            {"icon": "coronavirus", "color": "tertiary", "name_en": "Viral Infection", "name_ur": "وائرل انفیکشن"},
            {"icon": "biotech", "color": "secondary", "name_en": "Bacterial Infection", "name_ur": "بیکٹیریل انفیکشن"},
            {"icon": "wb_sunny", "color": "primary", "name_en": "Heat Stroke", "name_ur": "گرمی لگنا"},
            {"icon": "vaccines", "color": "secondary", "name_en": "Post-Vaccination", "name_ur": "ٹیکے کے بعد"}
        ],
        "remedies": [
            {"icon": "local_drink", "name_en": "Drink Plenty of Fluids", "name_ur": "زیادہ مائعات پئیں"},
            {"icon": "bed", "name_en": "Get Plenty of Rest", "name_ur": "زیادہ آرام کریں"},
            {"icon": "ac_unit", "name_en": "Cool Compress", "name_ur": "ٹھنڈی پٹی رکھیں"}
        ],
        "medicines": [
            {"name": "Panadol", "generic": "Paracetamol", "timing": "Every 4-6 hours", "dosage": "Safe for fever", "urdu_note": "بخار کے لیے محفوظ۔"},
            {"name": "Disprin", "generic": "Aspirin", "timing": "After meals", "dosage": "Adults only", "urdu_note": "صرف بالغوں کے لیے۔"}
        ],
        "red_flags": [
            {"en": "Fever above 103°F", "ur": "بخار 103 سے زیادہ"},
            {"en": "Lasting more than 3 days", "ur": "3 دن سے زیادہ بخار"},
            {"en": "With rash or breathing trouble", "ur": "دانے یا سانس کی تکلیف"}
        ]
    },
    "cold": {
        "name_en": "Cold & Flu", "name_ur": "نزلہ زکام", "icon": "ac_unit",
        "intro_en": "Common cold usually resolves in 7-10 days with proper rest and care.",
        "intro_ur": "نزلہ 7-10 دن میں ٹھیک ہو جاتا ہے۔",
        "causes": [
            {"icon": "coronavirus", "color": "tertiary", "name_en": "Viral Infection", "name_ur": "وائرس"},
            {"icon": "thermostat", "color": "secondary", "name_en": "Weather Change", "name_ur": "موسمی تبدیلی"},
            {"icon": "shield", "color": "primary", "name_en": "Weak Immunity", "name_ur": "کمزور قوت مدافعت"},
            {"icon": "groups", "color": "secondary", "name_en": "Contact with Sick", "name_ur": "بیمار سے رابطہ"}
        ],
        "remedies": [
            {"icon": "local_cafe", "name_en": "Warm Tea/Soup", "name_ur": "گرم چائے یا سوپ"},
            {"icon": "spa", "name_en": "Steam Inhalation", "name_ur": "بھاپ لیں"},
            {"icon": "bed", "name_en": "Plenty of Rest", "name_ur": "آرام کریں"}
        ],
        "medicines": [
            {"name": "Coldrex", "generic": "Paracetamol + Phenylephrine", "timing": "Every 6 hours", "dosage": "Max 4 doses/day", "urdu_note": "نزلے کے لیے بہترین۔"},
            {"name": "Panadol Cold & Flu", "generic": "Paracetamol + Caffeine", "timing": "Every 4-6 hours", "dosage": "Avoid at night", "urdu_note": "رات کو نہ لیں۔"}
        ],
        "red_flags": [
            {"en": "High fever above 102°F", "ur": "تیز بخار"},
            {"en": "Difficulty breathing", "ur": "سانس میں تکلیف"},
            {"en": "Symptoms over 10 days", "ur": "10 دن سے زیادہ علامات"}
        ]
    },
    "cough": {
        "name_en": "Cough", "name_ur": "کھانسی", "icon": "air",
        "intro_en": "Most coughs resolve within 1-2 weeks.",
        "intro_ur": "اکثر کھانسی 1-2 ہفتوں میں ٹھیک ہو جاتی ہے۔",
        "causes": [
            {"icon": "coronavirus", "color": "tertiary", "name_en": "Cold/Flu", "name_ur": "نزلہ زکام"},
            {"icon": "smoking_rooms", "color": "secondary", "name_en": "Smoke/Pollution", "name_ur": "دھواں"},
            {"icon": "eco", "color": "primary", "name_en": "Allergies", "name_ur": "الرجی"},
            {"icon": "water_drop", "color": "secondary", "name_en": "Dry Throat", "name_ur": "خشک گلا"}
        ],
        "remedies": [
            {"icon": "local_cafe", "name_en": "Honey + Warm Water", "name_ur": "شہد اور نیم گرم پانی"},
            {"icon": "spa", "name_en": "Steam Inhalation", "name_ur": "بھاپ لیں"},
            {"icon": "local_drink", "name_en": "Warm Fluids", "name_ur": "گرم مائعات"}
        ],
        "medicines": [
            {"name": "Hydrillin", "generic": "Diphenhydramine", "timing": "At bedtime", "dosage": "1 teaspoon", "urdu_note": "رات کو 1 چمچ۔"},
            {"name": "Cofsils", "generic": "Lozenges", "timing": "As needed", "dosage": "Max 8/day", "urdu_note": "ضرورت پر چوسیں۔"}
        ],
        "red_flags": [
            {"en": "Coughing blood", "ur": "خون کے ساتھ کھانسی"},
            {"en": "Cough lasting over 3 weeks", "ur": "3 ہفتے سے زیادہ کھانسی"},
            {"en": "Severe chest pain", "ur": "سینے میں شدید درد"}
        ]
    },
    "sore-throat": {
        "name_en": "Sore Throat", "name_ur": "گلے کی خراش", "icon": "sentiment_dissatisfied",
        "intro_en": "Sore throat is often caused by viral infections and heals within a few days.",
        "intro_ur": "گلے کی خراش عام طور پر وائرس کی وجہ سے ہوتی ہے۔",
        "causes": [
            {"icon": "coronavirus", "color": "tertiary", "name_en": "Viral Infection", "name_ur": "وائرس"},
            {"icon": "thermostat", "color": "secondary", "name_en": "Cold Weather", "name_ur": "ٹھنڈا موسم"},
            {"icon": "smoking_rooms", "color": "primary", "name_en": "Pollution", "name_ur": "آلودگی"},
            {"icon": "water_drop", "color": "secondary", "name_en": "Dry Air", "name_ur": "خشک ہوا"}
        ],
        "remedies": [
            {"icon": "local_drink", "name_en": "Warm Salt Water Gargle", "name_ur": "نمک ملا گرم پانی"},
            {"icon": "local_cafe", "name_en": "Honey + Lemon Tea", "name_ur": "شہد لیمن چائے"},
            {"icon": "spa", "name_en": "Steam Inhalation", "name_ur": "بھاپ لیں"}
        ],
        "medicines": [
            {"name": "Strepsils", "generic": "Lozenges", "timing": "Every 2-3 hours", "dosage": "Max 12/day", "urdu_note": "گلے کی خراش کے لیے۔"},
            {"name": "Panadol", "generic": "Paracetamol", "timing": "Every 4-6 hours", "dosage": "For pain relief", "urdu_note": "درد کے لیے لیں۔"}
        ],
        "red_flags": [
            {"en": "Difficulty swallowing", "ur": "نگلنے میں دشواری"},
            {"en": "High fever with sore throat", "ur": "تیز بخار کے ساتھ"},
            {"en": "White patches in throat", "ur": "گلے میں سفید دھبے"}
        ]
    },
    "stomach": {
        "name_en": "Stomach Pain", "name_ur": "پیٹ درد", "icon": "gastroenterology",
        "intro_en": "Most stomach pain is mild and resolves with simple home care.",
        "intro_ur": "پیٹ درد اکثر گھریلو علاج سے ٹھیک ہو جاتا ہے۔",
        "causes": [
            {"icon": "restaurant", "color": "tertiary", "name_en": "Indigestion", "name_ur": "بدہضمی"},
            {"icon": "local_fire_department", "color": "secondary", "name_en": "Acidity", "name_ur": "تیزابیت"},
            {"icon": "coronavirus", "color": "primary", "name_en": "Stomach Bug", "name_ur": "انفیکشن"},
            {"icon": "psychology", "color": "secondary", "name_en": "Stress", "name_ur": "ذہنی دباؤ"}
        ],
        "remedies": [
            {"icon": "local_drink", "name_en": "Warm Water", "name_ur": "گرم پانی پئیں"},
            {"icon": "self_care", "name_en": "Gentle Massage", "name_ur": "ہلکا مساج"},
            {"icon": "no_food", "name_en": "Light Diet", "name_ur": "ہلکی غذا لیں"}
        ],
        "medicines": [
            {"name": "Risek", "generic": "Omeprazole", "timing": "Before breakfast", "dosage": "Once daily", "urdu_note": "ناشتے سے پہلے 1 گولی۔"},
            {"name": "Gaviscon", "generic": "Antacid", "timing": "After meals", "dosage": "1-2 tablets", "urdu_note": "کھانے کے بعد لیں۔"}
        ],
        "red_flags": [
            {"en": "Severe sudden pain", "ur": "اچانک شدید درد"},
            {"en": "Vomiting blood", "ur": "خون کی قے"},
            {"en": "Pain with high fever", "ur": "تیز بخار کے ساتھ درد"}
        ]
    },
    "acidity": {
        "name_en": "Acidity", "name_ur": "تیزابیت", "icon": "local_fire_department",
        "intro_en": "Acidity occurs when stomach acid flows back. Common after spicy food or stress.",
        "intro_ur": "تیزابیت معدے کا تیزاب اوپر آنے سے ہوتی ہے۔",
        "causes": [
            {"icon": "restaurant", "color": "tertiary", "name_en": "Spicy Food", "name_ur": "مرچ مصالحے"},
            {"icon": "schedule", "color": "secondary", "name_en": "Skipping Meals", "name_ur": "کھانا چھوڑنا"},
            {"icon": "psychology", "color": "primary", "name_en": "Stress", "name_ur": "ذہنی دباؤ"},
            {"icon": "local_cafe", "color": "secondary", "name_en": "Tea/Coffee", "name_ur": "چائے کافی"}
        ],
        "remedies": [
            {"icon": "local_drink", "name_en": "Cold Milk", "name_ur": "ٹھنڈا دودھ"},
            {"icon": "spa", "name_en": "Eat Slowly", "name_ur": "آرام سے کھائیں"},
            {"icon": "no_food", "name_en": "Avoid Spicy Food", "name_ur": "مصالحے سے پرہیز"}
        ],
        "medicines": [
            {"name": "Risek", "generic": "Omeprazole", "timing": "Before breakfast", "dosage": "Once daily", "urdu_note": "صبح خالی پیٹ لیں۔"},
            {"name": "Gaviscon", "generic": "Antacid", "timing": "After meals", "dosage": "1-2 tablets", "urdu_note": "کھانے کے بعد۔"}
        ],
        "red_flags": [
            {"en": "Severe chest pain", "ur": "سینے میں شدید درد"},
            {"en": "Difficulty swallowing", "ur": "نگلنے میں دشواری"},
            {"en": "Frequent vomiting", "ur": "بار بار قے"}
        ]
    },
    "body-ache": {
        "name_en": "Body Ache", "name_ur": "جسم درد", "icon": "accessibility_new",
        "intro_en": "Body aches are common with infections, fatigue, or muscle strain.",
        "intro_ur": "جسم درد انفیکشن، تھکاوٹ یا پٹھوں کی کھنچاوٹ سے ہوتا ہے۔",
        "causes": [
            {"icon": "coronavirus", "color": "tertiary", "name_en": "Viral Fever", "name_ur": "وائرل بخار"},
            {"icon": "fitness_center", "color": "secondary", "name_en": "Overexertion", "name_ur": "زیادہ کام"},
            {"icon": "bed", "color": "primary", "name_en": "Poor Sleep", "name_ur": "نیند کی کمی"},
            {"icon": "water_drop", "color": "secondary", "name_en": "Dehydration", "name_ur": "پانی کی کمی"}
        ],
        "remedies": [
            {"icon": "bed", "name_en": "Rest Well", "name_ur": "آرام کریں"},
            {"icon": "spa", "name_en": "Warm Bath", "name_ur": "گرم پانی سے غسل"},
            {"icon": "self_care", "name_en": "Light Massage", "name_ur": "ہلکا مساج"}
        ],
        "medicines": [
            {"name": "Panadol", "generic": "Paracetamol", "timing": "Every 4-6 hours", "dosage": "Max 8/day", "urdu_note": "درد کے لیے۔"},
            {"name": "Brufen", "generic": "Ibuprofen", "timing": "After meals", "dosage": "3 times daily", "urdu_note": "کھانے کے بعد لیں۔"}
        ],
        "red_flags": [
            {"en": "Severe muscle weakness", "ur": "شدید کمزوری"},
            {"en": "Pain with high fever", "ur": "تیز بخار کے ساتھ"},
            {"en": "Sudden severe pain", "ur": "اچانک شدید درد"}
        ]
    },
    "diarrhea": {
        "name_en": "Diarrhea", "name_ur": "اسہال", "icon": "water_drop",
        "intro_en": "Diarrhea usually resolves in a few days. Stay hydrated.",
        "intro_ur": "اسہال چند دنوں میں ٹھیک ہو جاتا ہے۔ پانی کی کمی نہ ہونے دیں۔",
        "causes": [
            {"icon": "restaurant", "color": "tertiary", "name_en": "Bad Food", "name_ur": "خراب کھانا"},
            {"icon": "coronavirus", "color": "secondary", "name_en": "Infection", "name_ur": "انفیکشن"},
            {"icon": "water_drop", "color": "primary", "name_en": "Bad Water", "name_ur": "ناپاک پانی"},
            {"icon": "psychology", "color": "secondary", "name_en": "Stress", "name_ur": "ذہنی دباؤ"}
        ],
        "remedies": [
            {"icon": "local_drink", "name_en": "ORS / Salt-Sugar Water", "name_ur": "او آر ایس پئیں"},
            {"icon": "no_food", "name_en": "Avoid Heavy Food", "name_ur": "بھاری کھانا نہ کھائیں"},
            {"icon": "rice_bowl", "name_en": "Rice + Curd", "name_ur": "چاول دہی"}
        ],
        "medicines": [
            {"name": "ORS", "generic": "Rehydration Salts", "timing": "After each loose stool", "dosage": "1 sachet in 1L water", "urdu_note": "ہر بار اسہال کے بعد۔"},
            {"name": "Imodium", "generic": "Loperamide", "timing": "After loose stool", "dosage": "Adults only", "urdu_note": "صرف بالغوں کے لیے۔"}
        ],
        "red_flags": [
            {"en": "Blood in stool", "ur": "اسہال میں خون"},
            {"en": "Severe dehydration", "ur": "شدید پانی کی کمی"},
            {"en": "Diarrhea over 3 days", "ur": "3 دن سے زیادہ اسہال"}
        ]
    },
    "allergies": {
        "name_en": "Allergies", "name_ur": "الرجی", "icon": "eco",
        "intro_en": "Allergies cause sneezing, itching, or rash. Avoid the trigger and take antihistamines.",
        "intro_ur": "الرجی سے چھینکیں، خارش یا دانے ہو سکتے ہیں۔",
        "causes": [
            {"icon": "eco", "color": "tertiary", "name_en": "Pollen/Dust", "name_ur": "گرد و غبار"},
            {"icon": "pets", "color": "secondary", "name_en": "Pet Hair", "name_ur": "جانوروں کے بال"},
            {"icon": "restaurant", "color": "primary", "name_en": "Food Allergy", "name_ur": "کھانے کی الرجی"},
            {"icon": "medication", "color": "secondary", "name_en": "Medicine", "name_ur": "دوا کی الرجی"}
        ],
        "remedies": [
            {"icon": "shower", "name_en": "Wash Exposed Areas", "name_ur": "متاثرہ جگہ دھوئیں"},
            {"icon": "ac_unit", "name_en": "Cold Compress", "name_ur": "ٹھنڈی پٹی"},
            {"icon": "no_food", "name_en": "Avoid Triggers", "name_ur": "وجہ سے بچیں"}
        ],
        "medicines": [
            {"name": "Avil", "generic": "Pheniramine", "timing": "Once daily", "dosage": "1 tablet", "urdu_note": "دن میں 1 گولی۔"},
            {"name": "Telfast", "generic": "Fexofenadine", "timing": "Once daily", "dosage": "Non-drowsy", "urdu_note": "نیند نہیں آتی۔"}
        ],
        "red_flags": [
            {"en": "Difficulty breathing", "ur": "سانس کی تکلیف"},
            {"en": "Swelling of face/throat", "ur": "چہرے کی سوجن"},
            {"en": "Severe full-body rash", "ur": "پورے جسم پر دانے"}
        ]
    }
}

ISSUE_KEYWORDS = {
    "headache": ["headache", "head pain", "sar dard", "sir dard", "migraine"],
    "fever": ["fever", "bukhar", "temperature", "high fever", "feeling hot"],
    "cold": ["cold", "flu", "nazla", "zukam", "runny nose", "sneezing"],
    "cough": ["cough", "khansi", "dry cough", "wet cough"],
    "sore-throat": ["sore throat", "throat pain", "gala dard", "gale ki kharash"],
    "stomach": ["stomach", "stomach pain", "pet dard", "pait dard", "abdomen"],
    "acidity": ["acidity", "tezabiyat", "heartburn", "acid reflux", "gas", "burning"],
    "body-ache": ["body ache", "body pain", "jism dard", "muscle pain", "joint pain"],
    "diarrhea": ["diarrhea", "loose motion", "ishaal", "loose stool", "dast"],
    "allergies": ["allergy", "allergies", "rash", "itching", "khaarish"]
}


def _safe_str(value, max_len=500) -> str:
    if isinstance(value, dict):
        return ""
    return str(value or "")[:max_len]


def _safe_list(data: dict, key: str, lang: str) -> list:
    val = data.get(key, {})
    if isinstance(val, dict):
        result = val.get(lang, [])
        if isinstance(result, list):
            return [str(i)[:100] for i in result]
        if isinstance(result, str):
            return [result]
    return []


def format_gemini_response(data: dict) -> dict:
    return {
        "name": _safe_str(data.get("medicine_name", "Unknown Medicine"), 100),
        "name_urdu": _safe_str(data.get("urdu_name", ""), 100),
        "tags": data.get("tags", ["Medicine"]),
        "uses_en": _safe_str(data.get("uses", {}).get("en", "") if isinstance(data.get("uses"), dict) else ""),
        "uses_ur": _safe_str(data.get("uses", {}).get("ur", "") if isinstance(data.get("uses"), dict) else ""),
        "how_to_take_en": _safe_str(data.get("how_to_take", {}).get("en", "") if isinstance(data.get("how_to_take"), dict) else ""),
        "how_to_take_ur": _safe_str(data.get("how_to_take", {}).get("ur", "") if isinstance(data.get("how_to_take"), dict) else ""),
        "dosage_en": _safe_str(data.get("dosage", {}).get("en", "") if isinstance(data.get("dosage"), dict) else ""),
        "dosage_ur": _safe_str(data.get("dosage", {}).get("ur", "") if isinstance(data.get("dosage"), dict) else ""),
        "side_effects_en": _safe_list(data, "side_effects", "en"),
        "side_effects_ur": _safe_list(data, "side_effects", "ur"),
        "warnings_en": _safe_str(data.get("warnings", {}).get("en", "") if isinstance(data.get("warnings"), dict) else ""),
        "warnings_ur": _safe_str(data.get("warnings", {}).get("ur", "") if isinstance(data.get("warnings"), dict) else ""),
        "full_text_en": f"{data.get('medicine_name', '')}. {data.get('uses', {}).get('en', '') if isinstance(data.get('uses'), dict) else ''}",
        "full_text_ur": _safe_str(data.get("urdu_name", ""), 100),
    }


def _fallback_medicine(error: str = "") -> dict:
    return {
        "name": "Information Unavailable",
        "name_urdu": "معلومات دستیاب نہیں",
        "tags": ["Error"],
        "uses_en": "Could not fetch medicine information. Please try again or consult a pharmacist.",
        "uses_ur": "معذرت، اس وقت معلومات حاصل نہیں ہو سکیں۔ دوبارہ کوشش کریں یا کیمسٹ سے رابطہ کریں۔",
        "how_to_take_en": "Please consult a healthcare professional.",
        "how_to_take_ur": "براہ کرم ڈاکٹر سے مشورہ کریں۔",
        "dosage_en": "Not available.",
        "dosage_ur": "دستیاب نہیں۔",
        "side_effects_en": ["Information not available"],
        "side_effects_ur": ["معلومات دستیاب نہیں"],
        "warnings_en": "Always consult your doctor before taking any medicine.",
        "warnings_ur": "کوئی بھی دوا لینے سے پہلے ڈاکٹر سے مشورہ کریں۔",
        "full_text_en": "Information not available. Please try again.",
        "full_text_ur": "معلومات دستیاب نہیں۔",
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/common-issues")
def common_issues():
    return render_template("common_issues.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/health-issue/<issue_name>")
def health_issue(issue_name):
    issue = HEALTH_ISSUES.get(issue_name)
    if not issue:
        return redirect(url_for("common_issues"))
    return render_template("health_issue.html", issue=issue)


@app.route("/test")
def test():
    return jsonify({"status": "DawaSaathi backend running"})


@app.route("/api/analyze-image", methods=["POST"])
def analyze_image():
    filepath = None
    try:
        field = "medicine_image" if "medicine_image" in request.files else "image"
        if field not in request.files:
            return jsonify({"error": "No image uploaded.", "error_ur": "کوئی تصویر نہیں ملی۔"}), 400

        file = request.files[field]
        if not file.filename or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Use PNG, JPG, JPEG, or WEBP.", "error_ur": "غلط فائل کی قسم۔"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        medicine_name = analyze_medicine_image(filepath)
        gemini_data = get_medicine_info(medicine_name)
        medicine = format_gemini_response(gemini_data)
        return render_template("result.html", medicine=medicine)

    except GeminiAPIError as e:
        logger.error(f"analyze_image GeminiAPIError: {e}")
        return render_template("result.html", medicine=_fallback_medicine(str(e)))
    except Exception as e:
        logger.error(f"analyze_image unexpected error: {e}")
        return jsonify({"error": "Unexpected error. Please try again."}), 500
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/search-medicine", methods=["POST"])
def search_medicine():
    try:
        if request.is_json:
            body = request.get_json()
            medicine_name = (body or {}).get("medicine_name", "").strip()
        else:
            medicine_name = request.form.get("medicine_name", "").strip()

        if not medicine_name:
            if request.is_json:
                return jsonify({"error": "medicine_name is required"}), 400
            return redirect(url_for("index"))

        medicine_name = sanitize_input(medicine_name, max_length=100)
        gemini_data = get_medicine_info(medicine_name)

        if request.is_json:
            return jsonify({"success": True, "data": gemini_data})

        medicine = format_gemini_response(gemini_data)
        return render_template("result.html", medicine=medicine)

    except GeminiAPIError as e:
        logger.error(f"search_medicine GeminiAPIError: {e}")
        if request.is_json:
            return jsonify({"error": str(e)}), 500
        return render_template("result.html", medicine=_fallback_medicine(str(e)))
    except Exception as e:
        logger.error(f"search_medicine unexpected error: {e}")
        return jsonify({"error": "Unexpected error. Please try again."}), 500


@app.route("/api/search-issue", methods=["POST"])
def search_issue():
    try:
        problem_text = sanitize_input(
            request.form.get("problem_text", "").strip().lower(), max_length=500
        )
        if not problem_text:
            return redirect(url_for("common_issues"))

        for issue_key, keywords in ISSUE_KEYWORDS.items():
            if any(kw in problem_text for kw in keywords):
                return redirect(url_for("health_issue", issue_name=issue_key))

        return redirect(url_for("common_issues"))

    except Exception as e:
        logger.error(f"search_issue error: {e}")
        return redirect(url_for("common_issues"))


@app.route("/api/symptom-search", methods=["POST"])
def symptom_search():
    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "Request body required"}), 400

        symptoms = sanitize_input(body.get("symptoms", ""), max_length=500)
        age = sanitize_input(body.get("age", "adult"), max_length=20)
        severity = sanitize_input(body.get("severity", "mild"), max_length=20)

        if not symptoms:
            return jsonify({"error": "Symptoms are required"}), 400

        result = get_medicine_from_symptoms(symptoms, age, severity)
        return jsonify({"success": True, "data": result})

    except GeminiAPIError as e:
        logger.error(f"symptom_search GeminiAPIError: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"symptom_search unexpected error: {e}")
        return jsonify({"error": "Unexpected error. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)