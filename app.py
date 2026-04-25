import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from services.gemini_service import (
    analyze_medicine_image,
    get_medicine_info,
    get_medicine_from_symptoms,
)

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/test")
def test():
    return{"Testing" : "Dawa Sathi Working"}


@app.route("/api/analyze-image", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        medicine_name = analyze_medicine_image(filepath)
        result = get_medicine_info(medicine_name)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/search-medicine", methods=["POST"])
def search_medicine():
    body = request.get_json()
    if not body or "medicine_name" not in body:
        return jsonify({"error": "medicine_name is required"}), 400

    medicine_name = body["medicine_name"].strip()
    if not medicine_name:
        return jsonify({"error": "medicine_name cannot be empty"}), 400

    try:
        result = get_medicine_info(medicine_name)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/symptom-search", methods=["POST"])
def symptom_search():
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)