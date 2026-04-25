# 💊 DawaSaathi (دوا ساتھی)

> **AI-Powered Bilingual Medicine Assistant for Pakistan**
> 
> *Built for every Pakistani who deserves to understand their medicine.*

[![Built with Flask](https://img.shields.io/badge/Built%20with-Flask-blue)](https://flask.palletsprojects.com/)
[![Powered by Grok](https://img.shields.io/badge/Powered%20by-Grok%20AI-black)](https://x.ai/)
[![Bilingual](https://img.shields.io/badge/Languages-English%20%2B%20Urdu-green)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎯 The Problem

- **240 million** Pakistanis need accessible medical information
- **40%** of the population is illiterate and can't read English labels
- **60%** don't fully understand the medicines they take daily

## ✨ The Solution

DawaSaathi uses **Grok AI (xAI)** to instantly translate any medicine into clear, bilingual information — through text or voice — with audio playback for illiterate users.

---

## 🚀 Features

### 🔍 Two Input Methods
- **⌨️ Type Name** — Search by medicine name in English or Urdu
- **🎤 Voice Input** — Speak the name (great for elderly users)

### 💚 Common Health Issues Guide
- **Smart AI-Powered Search** — Type "sar dard" or "fever ho raha hai" in any language
- **10 Daily Issues** — Headache, Fever, Cold, Cough, Stomach Pain, and more
- **Safe OTC Recommendations** — AI-curated medicines for each issue
- **Doctor Warnings** — Clear red flags requiring medical attention

### 🌐 Fully Bilingual
- English + Urdu side-by-side
- Proper Nastaliq script with RTL layout
- Voice playback in both languages

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS, Google Fonts |
| **Backend** | Python 3.x, Flask, Flask-CORS |
| **AI** | Grok AI (xAI), AI-Powered Searching |
| **Voice** | Web Speech API (Speech Recognition + Synthesis) |
| **Deployment** | Vercel / GCP |

---

## 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/dawasaathi.git
cd dawasaathi

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Then edit .env and add your GROK_API_KEY
# Get your key at: https://x.ai/api

# 4. Run the app
python app.py

# 5. Open in browser
# http://localhost:5000
```

---

## 📂 Project Structure

```
DawaSaathi/
├── app.py                      # Flask backend with all routes
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (GROK_API_KEY)
├── services/
│   └── grok_service.py         # Grok AI integration
├── templates/
│   ├── index.html              # Homepage with tabbed input
│   ├── common_issues.html      # Health issues browser
│   ├── about.html              # Project story page
│   ├── result.html             # Medicine info display
│   └── health_issue.html       # Health issue detail page
└── static/
    ├── css/
    ├── js/
    └── fonts/
```

---

## 🔌 API Endpoints

| Endpoint | Method | AI Used | Description |
|----------|--------|---------|-------------|
| `/` | GET | — | Homepage |
| `/common-issues` | GET | — | Health issues browser |
| `/about` | GET | — | About page |
| `/health-issue/<n>` | GET | — | Issue detail page |
| `/api/search-medicine` | POST | Grok AI | Get bilingual medicine info |
| `/api/symptom-search` | POST | Grok AI | OTC suggestions from symptoms |
| `/api/search-issue` | POST | AI-Powered Search | Smart symptom routing |

---

## 🎨 Design System

- **Primary**: `#00685F` (Teal — trust, calm)
- **Mint**: `#96F3E1` (Backgrounds, hover)
- **Background**: `#FFF8F5` (Warm off-white)
- **Coral**: `#C6495E` (Warnings, emergencies)
- **Fonts**: Inter (English) + Noto Nastaliq Urdu (Urdu)

---

## 📊 System Architecture

Three-tier design:
1. **Presentation Layer** — Flask templates with Tailwind CSS
2. **Application Layer** — Flask backend with route handling
3. **AI Service Layer** — Grok AI (xAI) APIs

> See `DawaSaathi-System-Design.drawio` for full architecture diagram.

---

## 🙏 Disclaimer

DawaSaathi provides AI-generated informational content only. **It does NOT replace professional medical advice, diagnosis, or treatment.** Always consult a qualified healthcare provider for medical decisions. In emergencies, call **1122**.

---

## 👥 Team

**Team Name:** ByteBrains  
**Team Lead:** Haider Nisar  
**Hackathon:** GDGoC Algoligence Hackathon

---

## 📜 License

MIT License — see [LICENSE](LICENSE) file.

---

<div align="center">

**Made with ❤️ for Pakistan 🇵🇰**

*Healthcare information should not require literacy or English fluency.*

</div>
