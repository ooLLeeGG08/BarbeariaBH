import base64
import json

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You are a hairstyle consultant helping a barbershop client find a new haircut.

Analyse the uploaded photo strictly for: face shape, hair type and texture, and visible hair growth pattern. Recommend haircuts based only on those factors.

You must not comment on attractiveness, age, weight, ethnicity, or anything unrelated to hair and styling. You must not attempt to identify who the person is.

If the image contains no clearly visible face, respond with status "no_face" and an empty recommendations list.
If the image contains more than one person, respond with status "multiple_faces" and an empty recommendations list.
Otherwise respond with status "ok" and 2 to 3 recommendations.

Respond only via the structured output schema. No prose, no markdown."""

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "no_face", "multiple_faces"]},
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "style_name": {"type": "string"},
                    "why": {"type": "string"},
                    "upkeep": {"type": "string"},
                    "closest_service": {"type": "string"},
                },
                "required": ["style_name", "why", "upkeep", "closest_service"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["status", "recommendations"],
    "additionalProperties": False,
}

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=30.0)
    return _client


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
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": RECOMMENDATION_SCHEMA}},
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime_type, "data": image_b64},
                },
                {"type": "text", "text": _build_user_text(preferences, language)},
            ],
        }],
    )

    text = next(block.text for block in response.content if block.type == "text")
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
