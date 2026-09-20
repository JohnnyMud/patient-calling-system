from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import LlmSettings

SINGLETON_SETTINGS_ID = "default"
DEFAULT_PROVIDER = "openai"
DEFAULT_OPENAI_MODEL = "gpt-5.1"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
SUPPORTED_PROVIDERS = frozenset({"openai", "gemini"})


@dataclass(frozen=True)
class ResolvedLlmConfig:
    provider: str
    api_key: str
    model: str
    emergency_model: str | None = None


def _read_env_file_value(key: str) -> str | None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text().splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == key:
            cleaned = value.strip().strip("\"'")
            if cleaned:
                return cleaned
    return None


def get_env_value(key: str) -> str | None:
    value = os.getenv(key)
    if value and value.strip():
        return value.strip()
    return _read_env_file_value(key)


def default_model_for_provider(provider: str) -> str:
    if provider == "gemini":
        return get_env_value("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    return get_env_value("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL


def env_api_key_for_provider(provider: str) -> str | None:
    if provider == "gemini":
        return get_env_value("GEMINI_API_KEY")
    return get_env_value("OPENAI_API_KEY")


def normalize_provider(provider: str | None) -> str:
    candidate = (provider or DEFAULT_PROVIDER).strip().lower()
    if candidate not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {candidate}")
    return candidate


def mask_api_key(api_key: str | None) -> tuple[bool, str | None]:
    if not api_key:
        return False, None
    last4 = api_key[-4:] if len(api_key) >= 4 else api_key
    return True, last4


def load_settings_row(db: Session) -> LlmSettings | None:
    return db.get(LlmSettings, SINGLETON_SETTINGS_ID)


def get_or_create_settings(db: Session) -> LlmSettings:
    row = load_settings_row(db)
    if row is not None:
        return row

    provider = normalize_provider(get_env_value("LLM_PROVIDER") or DEFAULT_PROVIDER)
    row = LlmSettings(
        id=SINGLETON_SETTINGS_ID,
        provider=provider,
        api_key=env_api_key_for_provider(provider),
        model=default_model_for_provider(provider),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def upsert_settings(
    db: Session,
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> LlmSettings:
    row = load_settings_row(db)
    if row is None:
        resolved_provider = normalize_provider(
            provider or get_env_value("LLM_PROVIDER") or DEFAULT_PROVIDER
        )
        row = LlmSettings(
            id=SINGLETON_SETTINGS_ID,
            provider=resolved_provider,
            api_key=None,
            model=default_model_for_provider(resolved_provider),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(row)

    if provider is not None:
        row.provider = normalize_provider(provider)

    if model is not None and model.strip():
        row.model = model.strip()

    # Empty / missing api_key leaves the existing key unchanged.
    if api_key is not None and api_key.strip():
        row.api_key = api_key.strip()

    if not row.model:
        row.model = default_model_for_provider(row.provider)

    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def resolve_config(db: Session | None = None) -> ResolvedLlmConfig:
    """Resolve provider/api_key/model from DB settings with env fallbacks."""
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None

    if db is not None:
        row = load_settings_row(db)
        if row is not None:
            provider = row.provider
            api_key = row.api_key
            model = row.model

    resolved_provider = normalize_provider(
        provider or get_env_value("LLM_PROVIDER") or DEFAULT_PROVIDER
    )
    resolved_api_key = (api_key or "").strip() or env_api_key_for_provider(resolved_provider) or ""
    resolved_model = (model or "").strip() or default_model_for_provider(resolved_provider)

    emergency_model = None
    if resolved_provider == "openai":
        emergency_model = get_env_value("OPENAI_EMERGENCY_MODEL") or resolved_model

    return ResolvedLlmConfig(
        provider=resolved_provider,
        api_key=resolved_api_key,
        model=resolved_model,
        emergency_model=emergency_model,
    )


def settings_to_read_dict(row: LlmSettings | None) -> dict:
    if row is None:
        provider = normalize_provider(get_env_value("LLM_PROVIDER") or DEFAULT_PROVIDER)
        env_key = env_api_key_for_provider(provider)
        api_key_set, api_key_last4 = mask_api_key(env_key)
        return {
            "provider": provider,
            "model": default_model_for_provider(provider),
            "api_key_set": api_key_set,
            "api_key_last4": api_key_last4,
            "updated_at": None,
        }

    effective_key = row.api_key or env_api_key_for_provider(row.provider)
    api_key_set, api_key_last4 = mask_api_key(effective_key)
    return {
        "provider": row.provider,
        "model": row.model or default_model_for_provider(row.provider),
        "api_key_set": api_key_set,
        "api_key_last4": api_key_last4,
        "updated_at": row.updated_at,
    }
