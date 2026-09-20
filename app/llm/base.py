from typing import Protocol, runtime_checkable


@runtime_checkable
class LlmProvider(Protocol):
    """Provider interface for agent replies and emergency classification."""

    def generate_reply(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> str:
        """Return a short phone-agent reply for the conversation."""

    def detect_emergency(
        self,
        messages: list[dict[str, str]],
        prompt: str,
    ) -> bool:
        """Return True when the conversation indicates a current medical emergency."""
