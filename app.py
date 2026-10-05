from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

from rules import extract_lexical_features, rule_based_score
from file_rules import extract_file_features, file_rule_based_score
from gemini_check import analyze_url_with_gemini, analyze_file_with_gemini
from chatbot import chat_with_assistant

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
@limiter.limit("10 per minute")
def analyze():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL cannot be empty"}), 400

    features = extract_lexical_features(url)
    rule_result = rule_based_score(features)
    ai_result = analyze_url_with_gemini(url, features)
    final_verdict = combine_results(rule_result, ai_result)

    return jsonify({
        "url": url,
        "rule_based": rule_result,
        "ai_based": ai_result,
        "final": final_verdict,
        "features": features,
    })


@app.route("/analyze-file", methods=["POST"])
@limiter.limit("10 per minute")
def analyze_file():
    data = request.get_json()
    filename = data.get("filename", "").strip()
    size = data.get("size", 0)
    sha256 = data.get("sha256", "").strip()

    if not filename:
        return jsonify({"error": "Filename cannot be empty"}), 400

    features = extract_file_features(filename, size, sha256)
    rule_result = file_rule_based_score(features)
    ai_result = analyze_file_with_gemini(features)
    final_verdict = combine_results(rule_result, ai_result)

    return jsonify({
        "filename": filename,
        "rule_based": rule_result,
        "ai_based": ai_result,
        "final": final_verdict,
        "features": features,
    })


@app.route("/chat", methods=["POST"])
@limiter.limit("15 per minute")
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    result = chat_with_assistant(message, history)
    return jsonify(result)


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests. Please slow down and try again in a minute."}), 429


def combine_results(rule_result: dict, ai_result: dict) -> dict:
    rule_score = rule_result["rule_score"]
    ai_verdict = ai_result.get("verdict", "unknown")
    ai_confidence = ai_result.get("confidence", 0)

    if ai_verdict == "phishing" or rule_score >= 60:
        label = "DANGER"
        message = "This looks high-risk. Avoid opening or entering any information."
    elif ai_verdict == "suspicious" or rule_score >= 30:
        label = "CAUTION"
        message = "Some suspicious signals were found. Proceed carefully."
    elif ai_verdict == "error" or ai_verdict == "unknown":
        label = "UNKNOWN"
        message = "We couldn't complete the analysis. Please verify manually."
    else:
        label = "SAFE"
        message = "No significant risk indicators were found."

    return {
        "label": label,
        "message": message,
        "rule_score": rule_score,
        "ai_confidence": ai_confidence,
    }


if __name__ == "__main__":
    app.run(debug=False, port=5000)