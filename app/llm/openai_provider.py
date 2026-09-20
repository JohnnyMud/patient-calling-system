import json
from urllib import error, request


def extract_openai_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text.strip()

    chunks: list[str] = []
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue

            content = item.get("content")
            if not isinstance(content, list):
                continue

            for content_item in content:
                if not isinstance(content_item, dict):
                    continue

                text = content_item.get("text")
                if isinstance(text, str):
                    chunks.append(text)

    return "".join(chunks).strip()


def parse_emergency_json(raw_text: str) -> bool:
    result = json.loads(raw_text)
    is_emergency = result.get("is_emergency")
    if not isinstance(is_emergency, bool):
        raise ValueError("Emergency detector returned an invalid schema")
    return is_emergency


class OpenAIProvider:
    """OpenAI Responses API provider (urllib, no SDK)."""

    def __init__(self, api_key: str, model: str, emergency_model: str | None = None):
        if not api_key:
            raise RuntimeError("OpenAI API key is not configured")
        self.api_key = api_key
        self.model = model
        self.emergency_model = emergency_model or model

    def _post_responses(self, body: dict) -> dict:
        url = "https://api.openai.com/v1/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        openai_request = request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(openai_request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise RuntimeError(f"OpenAI API error: {error_body}") from exc

    def generate_reply(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> str:
        data = self._post_responses(
            {
                "model": self.model,
                "instructions": system_prompt,
                "input": messages,
                "max_output_tokens": 120,
            }
        )
        response = extract_openai_text(data)
        return response or "I am sorry, I did not catch that. Could you repeat it?"

    def detect_emergency(
        self,
        messages: list[dict[str, str]],
        prompt: str,
    ) -> bool:
        data = self._post_responses(
            {
                "model": self.emergency_model,
                "instructions": prompt,
                "input": messages,
                "max_output_tokens": 50,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "emergency_detection",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "is_emergency": {"type": "boolean"},
                            },
                            "required": ["is_emergency"],
                            "additionalProperties": False,
                        },
                    }
                },
            }
        )
        raw_text = extract_openai_text(data)
        if not raw_text:
            raise ValueError("Emergency detector returned an empty response")
        return parse_emergency_json(raw_text)
