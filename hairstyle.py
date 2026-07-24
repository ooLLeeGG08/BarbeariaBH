import base64
import json
import os

import requests

GEMINI_URL = (
    'https://generativelanguage.googleapis.com/v1beta/'
    'models/gemini-flash-latest:generateContent'
)

SYSTEM_PROMPT = """You are a hairstyle consultant helping a barbershop client find a new haircut.

Analyse the uploaded photo strictly for: face shape, hair type and texture, and visible hair growth pattern. Recommend haircuts based only on those factors.

You must not comment on attractiveness, age, weight, ethnicity, or anything unrelated to hair and styling. You must not attempt to identify who the person is.

If the image contains no clearly visible face, respond with status "no_face" and an empty recommendations list.
If the image contains more than one person, respond with status "multiple_faces" and an empty recommendations list.
Otherwise respond with status "ok" and 2 to 3 recommendations.

Respond ONLY with a single JSON object in exactly this shape — no prose, no markdown fences, no explanation before or after it:
{"status": "ok" | "no_face" | "multiple_faces", "recommendations": [{"style_name": "...", "why": "...", "upkeep": "...", "closest_service": "..."}]}"""


def _build_user_text(preferences, language):
    instruction = "Respond in Portuguese." if language == "pt" else "Respond in English."
    parts = [instruction]
    if preferences:
        if preferences.get("maintenance"):
            parts.append(f"Preferred maintenance level: {preferences['maintenance']}.")
        if preferences.get("beard"):
            parts.append(f"Beard preference: {preferences['beard']}.")
        if preferences.get("length_goal"):
            parts.append(f"Hair length goal: {preferences['length_goal']}.")
    return " ".join(parts)


def analyze_hairstyle(image_bytes, mime_type, preferences=None, language="pt"):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    prompt_text = SYSTEM_PROMPT + "\n\n" + _build_user_text(preferences, language)

    payload = {
        'contents': [{
            'parts': [
                {'text': prompt_text},
                {
                    'inline_data': {
                        'mime_type': mime_type,
                        'data': image_b64,
                    }
                },
            ]
        }]
    }

    resp = requests.post(
        GEMINI_URL,
        headers={'x-goog-api-key': api_key, 'Content-Type': 'application/json'},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        text = data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        return {"status": "error", "recommendations": []}
    return _parse_result(text)


def _parse_result(text):
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return {"status": "error", "recommendations": []}
    if not isinstance(data, dict) or "status" not in data or "recommendations" not in data:
        return {"status": "error", "recommendations": []}
    return data
