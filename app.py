"""
DawaSaathi - Flask Backend (MERGED)
Combines: Gemini AI integration + Multi-page UI + Smart search
Run: python app.py
Open: http://localhost:5000
"""

import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Friend's Gemini service imports
from services.gemini_service import (
    analyze_medicine_image,
    get_medicine_info,
    get_medicine_from_symptoms,
)

# Load environment variables (.env file with GEMINI_API_KEY)
load_dotenv()

app = Flask(__name__)
CORS(app)

# File upload config (from friend's code)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# HEALTH ISSUES DATA (for /health-issue/<name> pages)
# This is fallback data if Gemini API fails
# ============================================================

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
            {"name": "Panadol", "generic": "Paracetamol", "timing": "Every 4-6 hours", "dosage": "Maximum 8 tablets per day", "urdu_note": "کھانے کے بعد 1-2 گولیاں لیں۔"},
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
        "intro_en": "Fever is the body's natural response to infection. Most fevers can be managed at home with rest and fluids.",
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
            {"name": "Panadol", "generic": "Paracetamol", "timing": "Every 4-6 hours", "dosage": "Safe for fever reduction", "urdu_note": "بخار کے لیے محفوظ۔"},
            {"name": "Disprin", "generic": "Aspirin", "timing": "After meals", "dosage": "Adults only", "urdu_note": "صرف بالغوں کے لیے۔"}
        ],
        "red_flags": [
            {"en": "Fever above 103°F (39.4°C)", "ur": "بخار 103 سے زیادہ"},
            {"en": "Lasting more than 3 days", "ur": "3 دن سے زیادہ بخار"},
            {"en": "With rash or breathing trouble", "ur": "دانے یا سانس کی تکلیف"}
        ]
    },
    "cold": {
        "name_en": "Cold & Flu", "name_ur": "نزلہ زکام", "icon": "ac_unit",
        "intro_en": "Common cold is a viral infection that usually resolves in 7-10 days with proper rest and care.",
        "intro_ur": "نزلہ ایک وائرل انفیکشن ہے جو 7-10 دن میں ٹھیک ہو جاتا ہے۔",
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
            {"name": "Coldrex", "generic": "Paracetamol + Phenylephrine", "timing": "Every 6 hours", "dosage": "Max 4 doses per day", "urdu_note": "نزلے کے لیے بہترین۔"},
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
        "intro_en": "Cough is a natural reflex to clear airways. Most coughs resolve within 1-2 weeks.",
        "intro_ur": "کھانسی ایک قدرتی عمل ہے۔ اکثر 1-2 ہفتوں میں ٹھیک ہو جاتی ہے۔",
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
            {"name": "Cofsils", "generic": "Lozenges", "timing": "As needed", "dosage": "Max 8 per day", "urdu_note": "ضرورت پر چوسیں۔"}
        ],
        "red_flags": [
            {"en": "Coughing blood", "ur": "خون کے ساتھ کھانسی"},
            {"en": "Cough lasting over 3 weeks", "ur": "3 ہفتے سے زیادہ کھانسی"},
            {"en": "Severe chest pain", "ur": "سینے میں شدید درد"}
        ]
    },
    "sore-throat": {
        "name_en": "Sore Throat", "name_ur": "گلے کی خراش", "icon": "sentiment_dissatisfied",
        "intro_en": "Sore throat is often caused by viral infections and usually heals within a few days.",
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
            {"name": "Strepsils", "generic": "Lozenges", "timing": "Every 2-3 hours", "dosage": "Max 12 per day", "urdu_note": "گلے کی خراش کے لیے۔"},
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
        "intro_en": "Stomach pain has many causes. Most cases are mild and resolve with simple home care.",
        "intro_ur": "پیٹ درد کی کئی وجوہات ہوتی ہیں، اکثر گھریلو علاج سے ٹھیک ہو جاتا ہے۔",
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
            {"name": "Panadol", "generic": "Paracetamol", "timing": "Every 4-6 hours", "dosage": "Max 8 per day", "urdu_note": "درد کے لیے۔"},
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
        "intro_en": "Diarrhea usually resolves in a few days. Stay hydrated to avoid weakness.",
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
            {"name": "Imodium", "generic": "Loperamide", "timing": "After loose stool", "dosage": "Adults only, 2 tabs first", "urdu_note": "صرف بالغوں کے لیے۔"}
        ],
        "red_flags": [
            {"en": "Blood in stool", "ur": "اسہال میں خون"},
            {"en": "Severe dehydration", "ur": "شدید پانی کی کمی"},
            {"en": "Diarrhea over 3 days", "ur": "3 دن سے زیادہ اسہال"}
        ]
    },
    "allergies": {
        "name_en": "Allergies", "name_ur": "الرجی", "icon": "eco",
        "intro_en": "Allergies cause sneezing, itching, or skin rash. Avoid the trigger and take antihistamines.",
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


# Smart search keywords for symptom-to-issue matching
ISSUE_KEYWORDS = {
    "headache": ["headache", "head pain", "head ache", "sar dard", "sir dard", "migraine", "head hurts"],
    "fever": ["fever", "buhaar", "bukhar", "temperature", "high fever", "feeling hot"],
    "cold": ["cold", "flu", "nzla", "nazla", "zukam", "runny nose", "stuffy nose", "sneezing"],
    "cough": ["cough", "khansi", "dry cough", "wet cough", "coughing"],
    "sore-throat": ["sore throat", "throat pain", "gala dard", "gale ki kharash", "throat hurts"],
    "stomach": ["stomach", "stomach pain", "pet dard", "pait dard", "tummy", "abdomen pain"],
    "acidity": ["acidity", "tezabiyat", "heartburn", "acid reflux", "gas", "burning"],
    "body-ache": ["body ache", "body pain", "jism dard", "muscle pain", "joint pain", "joron ka dard"],
    "diarrhea": ["diarrhea", "loose motion", "ishaal", "loose stool", "dast"],
    "allergies": ["allergy", "allergies", "rash", "itching", "skin allergy", "khaarish", "alergy"]
}


def format_gemini_response(gemini_data):
    """
    Convert Gemini API response to format expected by result.html template.
    Gemini returns flexible JSON, we map it to our template variables.
    """
    # Default structure for our template
    return {
        "name": gemini_data.get("name", "Unknown Medicine"),
        "name_urdu": gemini_data.get("name_urdu", gemini_data.get("name_ur", "")),
        "tags": gemini_data.get("tags", gemini_data.get("categories", ["Medicine"])),
        "uses_en": gemini_data.get("uses_en", gemini_data.get("uses", {}).get("en", "") if isinstance(gemini_data.get("uses"), dict) else gemini_data.get("uses", "")),
        "uses_ur": gemini_data.get("uses_ur", gemini_data.get("uses", {}).get("ur", "") if isinstance(gemini_data.get("uses"), dict) else ""),
        "how_to_take_en": gemini_data.get("how_to_take_en", gemini_data.get("how_to_take", {}).get("en", "") if isinstance(gemini_data.get("how_to_take"), dict) else gemini_data.get("how_to_take", "")),
        "how_to_take_ur": gemini_data.get("how_to_take_ur", gemini_data.get("how_to_take", {}).get("ur", "") if isinstance(gemini_data.get("how_to_take"), dict) else ""),
        "dosage_en": gemini_data.get("dosage_en", gemini_data.get("dosage", {}).get("en", "") if isinstance(gemini_data.get("dosage"), dict) else gemini_data.get("dosage", "")),
        "dosage_ur": gemini_data.get("dosage_ur", gemini_data.get("dosage", {}).get("ur", "") if isinstance(gemini_data.get("dosage"), dict) else ""),
        "side_effects_en": gemini_data.get("side_effects_en", gemini_data.get("side_effects", {}).get("en", []) if isinstance(gemini_data.get("side_effects"), dict) else (gemini_data.get("side_effects", []) if isinstance(gemini_data.get("side_effects"), list) else [])),
        "side_effects_ur": gemini_data.get("side_effects_ur", gemini_data.get("side_effects", {}).get("ur", []) if isinstance(gemini_data.get("side_effects"), dict) else []),
        "warnings_en": gemini_data.get("warnings_en", gemini_data.get("warnings", {}).get("en", "") if isinstance(gemini_data.get("warnings"), dict) else gemini_data.get("warnings", "")),
        "warnings_ur": gemini_data.get("warnings_ur", gemini_data.get("warnings", {}).get("ur", "") if isinstance(gemini_data.get("warnings"), dict) else ""),
        "full_text_en": gemini_data.get("full_text_en", f"{gemini_data.get('name', '')}. {gemini_data.get('uses_en', '')}"),
        "full_text_ur": gemini_data.get("full_text_ur", gemini_data.get("name_urdu", ""))
    }


# ============================================================
# PAGE ROUTES (Render HTML templates)
# ============================================================

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
    return {"Testing": "Dawa Sathi Working"}


# ============================================================
# FORM SUBMISSION ROUTES (HTML form -> Render result page)
# These are called by the homepage forms (Photo, Type, Speak)
# ============================================================

@app.route("/api/analyze-image", methods=["POST"])
def analyze_image():
    """Handle photo upload from homepage form. Uses Gemini Vision."""
    
    # Check both possible field names (template uses 'medicine_image')
    file_field = "medicine_image" if "medicine_image" in request.files else "image"
    
    if file_field not in request.files:
        return render_template("error.html", 
                             error_en="No image was uploaded. Please try again.",
                             error_ur="کوئی تصویر نہیں ملی۔") if _template_exists("error.html") else redirect(url_for("index"))
    
    file = request.files[file_field]
    
    if file.filename == "" or not allowed_file(file.filename):
        return redirect(url_for("index"))
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    try:
        # Call Gemini Vision API to identify the medicine
        medicine_name = analyze_medicine_image(filepath)
        # Then get full info about that medicine
        gemini_data = get_medicine_info(medicine_name)
        # Format for our template
        medicine = format_gemini_response(gemini_data)
        return render_template("result.html", medicine=medicine)
    except Exception as e:
        print(f"❌ Error in analyze_image: {e}")
        # Fallback: show a friendly error or default medicine
        return render_template("result.html", medicine=_get_fallback_medicine(str(e)))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/search-medicine", methods=["POST"])
def search_medicine():
    """Handle text/voice medicine search from homepage form."""
    
    # Support both form data (HTML form) and JSON (API call)
    if request.is_json:
        body = request.get_json()
        medicine_name = body.get("medicine_name", "").strip() if body else ""
    else:
        medicine_name = request.form.get("medicine_name", "").strip()
    
    if not medicine_name:
        return redirect(url_for("index"))
    
    try:
        # Call Gemini API to get medicine info
        gemini_data = get_medicine_info(medicine_name)
        medicine = format_gemini_response(gemini_data)
        
        # If JSON request (API style), return JSON
        if request.is_json:
            return jsonify({"success": True, "data": gemini_data})
        # If HTML form request, render the template
        return render_template("result.html", medicine=medicine)
    except Exception as e:
        print(f"❌ Error in search_medicine: {e}")
        if request.is_json:
            return jsonify({"error": str(e)}), 500
        return render_template("result.html", medicine=_get_fallback_medicine(str(e)))


@app.route("/api/search-issue", methods=["POST"])
def search_issue():
    """Smart search: matches user's free-text problem to a health issue page."""
    problem_text = request.form.get("problem_text", "").strip().lower()
    
    if not problem_text:
        return redirect(url_for("common_issues"))
    
    # Find best matching issue based on keywords
    matched_issue = None
    for issue_key, keywords in ISSUE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in problem_text:
                matched_issue = issue_key
                break
        if matched_issue:
            break
    
    if matched_issue:
        return redirect(url_for("health_issue", issue_name=matched_issue))
    else:
        # No keyword match — try Gemini AI for smarter matching
        try:
            gemini_result = get_medicine_from_symptoms(problem_text, "adult", "mild")
            # If Gemini returns useful info, you could create a dynamic page
            # For now, redirect back to common issues
            return redirect(url_for("common_issues"))
        except Exception as e:
            print(f"❌ Error in search_issue: {e}")
            return redirect(url_for("common_issues"))


# ============================================================
# JSON API ROUTE (for direct API usage / testing)
# ============================================================

@app.route("/api/symptom-search", methods=["POST"])
def symptom_search():
    """Friend's original symptom search API (returns JSON)."""
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body is required"}), 400
    
    symptoms = body.get("symptoms", "").strip()
    age = body.get("age", "adult").strip()
    severity = body.get("severity", "mild").strip()
    
    if not symptoms:
        return jsonify({"error": "symptoms are required"}), 400
    
    try:
        result = get_medicine_from_symptoms(symptoms, age, severity)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _template_exists(template_name):
    """Check if a template file exists."""
    try:
        app.jinja_env.get_template(template_name)
        return True
    except Exception:
        return False


def _get_fallback_medicine(error_msg):
    """Returns a fallback medicine when Gemini fails."""
    return {
        "name": "Information Unavailable",
        "name_urdu": "معلومات دستیاب نہیں",
        "tags": ["Error"],
        "uses_en": f"Sorry, we couldn't fetch medicine information at this time. Please try again or consult a pharmacist. Error: {error_msg}",
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
        "full_text_ur": "معلومات دستیاب نہیں۔"
    }



if __name__ == "__main__":
    app.run(debug=True, port=5000)