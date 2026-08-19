from app.api.websocket import (
    extract_openai_text,
    extract_transcript_message,
    extract_transcript_messages,
    should_persist_transcript,
)


def test_extract_transcript_messages_from_list():
    payload = {
        "transcript": [
            {"role": "agent", "content": "Hello, this is a reminder."},
            {"role": "patient", "content": "  I can still make it.  "},
            {"role": "user", "content": ""},
            "skip me",
        ]
    }

    assert extract_transcript_messages(payload) == [
        {"role": "assistant", "content": "Hello, this is a reminder."},
        {"role": "user", "content": "I can still make it."},
    ]


def test_extract_transcript_messages_from_flat_payload():
    payload = {"role": "caller", "content": "Can you repeat the time?"}
    assert extract_transcript_messages(payload) == [
        {"role": "user", "content": "Can you repeat the time?"},
    ]


def test_extract_transcript_message_returns_none_without_text():
    assert extract_transcript_message({"role": "user"}) is None


def test_should_persist_transcript():
    assert should_persist_transcript({"end_call": True}) is True
    assert should_persist_transcript({"event": "call_finished"}) is True
    assert should_persist_transcript({"interaction_type": "response_required"}) is False


def test_extract_openai_text_prefers_output_text():
    assert extract_openai_text({"output_text": "  Chest pain.  "}) == "Chest pain."


def test_extract_openai_text_joins_content_chunks():
    payload = {
        "output": [
            {
                "content": [
                    {"text": "I can help "},
                    {"text": "with that appointment."},
                ]
            }
        ]
    }
    assert extract_openai_text(payload) == "I can help with that appointment."
