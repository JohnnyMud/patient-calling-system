from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.llm.settings_store import (
    SINGLETON_SETTINGS_ID,
    settings_to_read_dict,
    upsert_settings,
)


def test_settings_to_read_dict_masks_key(monkeypatch):
    monkeypatch.setattr(
        "app.llm.settings_store.env_api_key_for_provider",
        lambda _provider: None,
    )
    row = SimpleNamespace(
        provider="openai",
        api_key="sk-secret-abcd",
        model="gpt-5.1",
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    result = settings_to_read_dict(row)
    assert result["api_key_set"] is True
    assert result["api_key_last4"] == "abcd"
    assert "api_key" not in result
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-5.1"


def test_settings_to_read_dict_env_fallback_when_no_row(monkeypatch):
    monkeypatch.setattr(
        "app.llm.settings_store.get_env_value",
        lambda key: {
            "LLM_PROVIDER": "gemini",
            "GEMINI_MODEL": "gemini-2.0-flash",
            "GEMINI_API_KEY": "gem-zzzz",
        }.get(key),
    )
    monkeypatch.setattr(
        "app.llm.settings_store.env_api_key_for_provider",
        lambda provider: "gem-zzzz" if provider == "gemini" else None,
    )
    monkeypatch.setattr(
        "app.llm.settings_store.default_model_for_provider",
        lambda provider: "gemini-2.0-flash" if provider == "gemini" else "gpt-5.1",
    )

    result = settings_to_read_dict(None)
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-2.0-flash"
    assert result["api_key_set"] is True
    assert result["api_key_last4"] == "zzzz"
    assert result["updated_at"] is None


def test_upsert_settings_creates_singleton_and_keeps_empty_key(monkeypatch):
    stored: dict = {}

    class FakeRow:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    fake_db = MagicMock()
    fake_db.get.return_value = None

    def add(row):
        stored["row"] = row

    def refresh(row):
        return row

    fake_db.add.side_effect = add
    fake_db.refresh.side_effect = refresh
    monkeypatch.setattr(
        "app.llm.settings_store.get_env_value",
        lambda key: "openai" if key == "LLM_PROVIDER" else None,
    )
    monkeypatch.setattr(
        "app.llm.settings_store.default_model_for_provider",
        lambda _provider: "gpt-5.1",
    )
    monkeypatch.setattr("app.llm.settings_store.LlmSettings", FakeRow)

    row = upsert_settings(
        fake_db,
        provider="openai",
        model="gpt-5.1",
        api_key="sk-initial-key",
    )
    assert row.id == SINGLETON_SETTINGS_ID
    assert row.api_key == "sk-initial-key"
    fake_db.commit.assert_called()

    # Second upsert with empty api_key must leave the existing key unchanged.
    fake_db.get.return_value = row
    updated = upsert_settings(fake_db, provider="gemini", model="gemini-2.0-flash", api_key="")
    assert updated.provider == "gemini"
    assert updated.model == "gemini-2.0-flash"
    assert updated.api_key == "sk-initial-key"


def test_upsert_settings_replaces_key_when_provided():
    row = SimpleNamespace(
        id=SINGLETON_SETTINGS_ID,
        provider="openai",
        api_key="old-key",
        model="gpt-5.1",
        updated_at=datetime.now(timezone.utc),
    )
    fake_db = MagicMock()
    fake_db.get.return_value = row

    updated = upsert_settings(fake_db, api_key="new-key-value")
    assert updated.api_key == "new-key-value"
    fake_db.commit.assert_called()
