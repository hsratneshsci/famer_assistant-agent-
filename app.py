from flask import Flask, request, jsonify, render_template, send_from_directory, redirect
import os, json, requests
from datetime import datetime
from bs4 import BeautifulSoup
from googletrans import Translator

app = Flask(__name__)
SHARED_FOLDER = r"C:\\sharing"
translator = Translator()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/data/<path:filename>')
def data_files(filename):
    return send_from_directory(SHARED_FOLDER, filename)

@app.route("/ask", methods=["POST"])
def ask_ai():
    question = request.form.get("question", "").lower()
    lang = request.form.get("lang", "en")

    qna_path = os.path.join(SHARED_FOLDER, "qna.json")
    if not os.path.exists(qna_path):
        return jsonify({"answer": "No knowledge base found.", "followups": []})

    with open(qna_path, "r", encoding="utf-8") as f:
        qna = json.load(f)

    try:
        for key in qna:
            if key in question:
                response = qna[key]
                translated_answer = translator.translate(response.get("answer", ""), dest=lang).text
                translated_followups = [translator.translate(f, dest=lang).text for f in response.get("followups", [])]
                return jsonify({"answer": translated_answer, "followups": translated_followups})

        headers = {"User-Agent": "Mozilla/5.0"}

        # Try Wikipedia summary first
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{question.replace(' ', '%20')}"
        wiki_res = requests.get(wiki_url, headers=headers)
        if wiki_res.status_code == 200 and 'extract' in wiki_res.json():
            data = wiki_res.json()
            summary = data.get("extract", "No detailed info found.")
            translated_summary = translator.translate(summary, dest=lang).text
            translated_followups = [translator.translate(t, dest=lang).text for t in ["Would you like more details?", "Want help in another language?"]]
            return jsonify({"answer": translated_summary, "followups": translated_followups})

        # DuckDuckGo fallback
        ddg_res = requests.get(f"https://duckduckgo.com/html/?q={question}", headers=headers)
        soup = BeautifulSoup(ddg_res.text, "html.parser")
        result = soup.select_one(".result__snippet")
        answer = result.get_text() if result else "Sorry, I couldn't find anything useful online."
        translated_answer = translator.translate(answer, dest=lang).text
        translated_followups = [translator.translate(f, dest=lang).text for f in ["Want a deeper answer?", "Try asking differently."]]

        return jsonify({"answer": translated_answer, "followups": translated_followups})

    except Exception as e:
        print("❌ Online search failed:", e)
        return jsonify({"answer": "No internet access or search failed.", "followups": []})

@app.route("/upload", methods=["POST"])
def upload():
    if 'photo' not in request.files:
        return "No file part", 400
    file = request.files['photo']
    if file.filename == '':
        return "No selected file", 400
    if file:
        file_path = os.path.join(SHARED_FOLDER, "scan.jpg")
        file.save(file_path)
        return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    otp = request.form.get("otp")
    if otp:
        return redirect("/")
    return "Invalid OTP", 400

if __name__ == "__main__":
    os.makedirs(SHARED_FOLDER, exist_ok=True)
    for file in ["user.json", "qna.json"]:
        f_path = os.path.join(SHARED_FOLDER, file)
        if not os.path.exists(f_path):
            with open(f_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
    app.run(host="0.0.0.0", port=5000, debug=True)