from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.llm.base import LlmProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.settings_store import resolve_config


def build_provider(
    provider: str,
    api_key: str,
    model: str,
    emergency_model: str | None = None,
) -> LlmProvider:
    if provider == "gemini":
        return GeminiProvider(api_key=api_key, model=model)
    return OpenAIProvider(
        api_key=api_key,
        model=model,
        emergency_model=emergency_model,
    )


def get_llm_provider(db: Session | None = None) -> LlmProvider:
    """Return an LLM provider from DB settings with environment fallbacks."""
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        config = resolve_config(session)
        return build_provider(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            emergency_model=config.emergency_model,
        )
    finally:
        if owns_session:
            session.close()
