import json
from urllib import error, request
from urllib.parse import quote

from app.llm.openai_provider import parse_emergency_json


def extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""

    first = candidates[0]
    if not isinstance(first, dict):
        return ""

    content = first.get("content")
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    chunks: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        text = part.get("text")
        if isinstance(text, str):
            chunks.append(text)

    return "".join(chunks).strip()


def to_gemini_contents(messages: list[dict[str, str]]) -> list[dict]:
    contents: list[dict] = []
    for message in messages:
        role = message.get("role", "user")
        gemini_role = "model" if role == "assistant" else "user"
        contents.append(
            {
                "role": gemini_role,
                "parts": [{"text": message.get("content", "")}],
            }
        )
    return contents


class GeminiProvider:
    """Google Gemini generateContent REST provider (urllib, no SDK)."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise RuntimeError("Gemini API key is not configured")
        self.api_key = api_key
        self.model = model

    def _post_generate(self, body: dict) -> dict:
        encoded_model = quote(self.model, safe="")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{encoded_model}:generateContent?key={quote(self.api_key, safe='')}"
        )
        headers = {"Content-Type": "application/json"}
        gemini_request = request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(gemini_request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise RuntimeError(f"Gemini API error: {error_body}") from exc

    def generate_reply(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> str:
        data = self._post_generate(
            {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": to_gemini_contents(messages),
                "generationConfig": {"maxOutputTokens": 120},
            }
        )
        response = extract_gemini_text(data)
        return response or "I am sorry, I did not catch that. Could you repeat it?"

    def detect_emergency(
        self,
        messages: list[dict[str, str]],
        prompt: str,
    ) -> bool:
        data = self._post_generate(
            {
                "systemInstruction": {"parts": [{"text": prompt}]},
                "contents": to_gemini_contents(messages),
                "generationConfig": {
                    "maxOutputTokens": 50,
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "OBJECT",
                        "properties": {
                            "is_emergency": {"type": "BOOLEAN"},
                        },
                        "required": ["is_emergency"],
                    },
                },
            }
        )
        raw_text = extract_gemini_text(data)
        if not raw_text:
            raise ValueError("Emergency detector returned an empty response")
        return parse_emergency_json(raw_text)
