from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.llm.factory import build_provider, get_llm_provider
from app.llm.gemini_provider import GeminiProvider, extract_gemini_text, to_gemini_contents
from app.llm.openai_provider import OpenAIProvider, extract_openai_text, parse_emergency_json
from app.llm import settings_store


def test_build_provider_selects_openai():
    provider = build_provider("openai", api_key="sk-test", model="gpt-5.1")
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-5.1"


def test_build_provider_selects_gemini():
    provider = build_provider("gemini", api_key="gem-test", model="gemini-2.0-flash")
    assert isinstance(provider, GeminiProvider)
    assert provider.model == "gemini-2.0-flash"


def test_get_llm_provider_uses_env_when_db_empty(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "gem-from-env")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    monkeypatch.setattr(settings_store, "_read_env_file_value", lambda _key: None)

    fake_db = MagicMock()
    fake_db.get.return_value = None

    provider = get_llm_provider(fake_db)
    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "gem-from-env"
    assert provider.model == "gemini-2.0-flash"


def test_get_llm_provider_prefers_db_row(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setattr(settings_store, "_read_env_file_value", lambda _key: None)

    row = SimpleNamespace(
        provider="gemini",
        api_key="gem-db",
        model="gemini-2.0-flash",
    )
    fake_db = MagicMock()
    fake_db.get.return_value = row

    provider = get_llm_provider(fake_db)
    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "gem-db"


def test_extract_openai_text_and_emergency_parse():
    assert extract_openai_text({"output_text": " hi "}) == "hi"
    assert parse_emergency_json('{"is_emergency": true}') is True
    assert parse_emergency_json('{"is_emergency": false}') is False
    with pytest.raises(ValueError):
        parse_emergency_json('{"is_emergency": "yes"}')


def test_extract_gemini_text_and_role_mapping():
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello "}, {"text": "there"}],
                }
            }
        ]
    }
    assert extract_gemini_text(payload) == "Hello there"
    assert to_gemini_contents(
        [
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Yes"},
        ]
    ) == [
        {"role": "model", "parts": [{"text": "Hi"}]},
        {"role": "user", "parts": [{"text": "Yes"}]},
    ]


def test_normalize_provider_rejects_unknown():
    with pytest.raises(ValueError):
        settings_store.normalize_provider("claude")


def test_mask_api_key():
    assert settings_store.mask_api_key(None) == (False, None)
    assert settings_store.mask_api_key("abcd1234") == (True, "1234")
