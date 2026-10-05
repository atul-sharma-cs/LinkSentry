import os
import json
from google import genai
from gemini_retry import call_with_retry, is_transient_error

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.5-flash"

URL_SYSTEM_PROMPT = """You are a cybersecurity assistant specialized in phishing URL analysis.
You will be given a URL along with some pre-computed lexical features about it.
Respond ONLY with a valid JSON object in this exact format, with no other text
before or after:

{
  "verdict": "phishing" | "suspicious" | "safe",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentence plain-language explanation>",
  "red_flags": ["<short flag 1>", "<short flag 2>", ...]
}

Guidelines:
- "phishing": strong evidence of malicious intent (brand impersonation, typosquatting, credential harvesting patterns)
- "suspicious": some concerning signals but not conclusive
- "safe": no meaningful red flags found
- Be specific in reasoning (mention the actual domain, brand name if impersonated, etc.)
"""

FILE_SYSTEM_PROMPT = """You are a cybersecurity assistant specialized in file-risk triage based
ONLY on filename, extension, size, and hash metadata (you never see file contents).
Respond ONLY with a valid JSON object in this exact format, with no other text
before or after:

{
  "verdict": "phishing" | "suspicious" | "safe",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentence plain-language explanation>",
  "red_flags": ["<short flag 1>", "<short flag 2>", ...]
}

Guidelines:
- Treat "phishing" here as "high risk / likely malicious".
- Flag double extensions (invoice.pdf.exe), executable/script extensions, and
  filenames that impersonate common document types or brands.
- Be explicit that this is a metadata-only assessment, not a full malware scan.
"""


def _call_gemini(system_prompt: str, user_message: str) -> dict:
    try:
        response = call_with_retry(lambda: client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.2,
            },
        ))

        raw_text = response.text.strip()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        return json.loads(raw_text)

    except json.JSONDecodeError:
        return {
            "verdict": "unknown",
            "confidence": 0,
            "reasoning": "Could not parse the AI response. Please try again.",
            "red_flags": [],
        }
    except Exception as e:
        if is_transient_error(e):
            reasoning = "The AI service is temporarily busy handling high demand. Please try scanning again in a few seconds."
        else:
            reasoning = f"The AI check could not be completed ({str(e)}). The rule-based result above is still valid."
        return {
            "verdict": "error",
            "confidence": 0,
            "reasoning": reasoning,
            "red_flags": [],
        }


def analyze_url_with_gemini(url: str, lexical_features: dict) -> dict:
    user_message = f"""Analyze this URL for phishing indicators:

URL: {url}

Pre-computed lexical features:
{json.dumps(lexical_features, indent=2)}

Respond with the JSON object only."""

    return _call_gemini(URL_SYSTEM_PROMPT, user_message)


def analyze_file_with_gemini(file_features: dict) -> dict:
    user_message = f"""Analyze this file's metadata for risk indicators:

{json.dumps(file_features, indent=2)}

Respond with the JSON object only."""

    return _call_gemini(FILE_SYSTEM_PROMPT, user_message)