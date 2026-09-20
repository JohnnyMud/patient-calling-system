"""LLM provider abstraction for call-agent replies and emergency detection."""

from app.llm.factory import get_llm_provider
from app.llm.base import LlmProvider

__all__ = ["LlmProvider", "get_llm_provider"]
