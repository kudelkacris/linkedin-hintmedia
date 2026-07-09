"""
llm/claude_adapter.py — Anthropic API adapter (optional dependency).

Requires: pip install anthropic
Requires: ANTHROPIC_API_KEY in environment or passed as api_key=

All commercial reasoning is done BEFORE this module runs.
This module only converts a structured prompt string into a text draft.
"""
from .adapter import LLMAdapter

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 600


class ClaudeAdapter(LLMAdapter):
    def __init__(self, api_key: str | None = None, model: str = _MODEL):
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "ClaudeAdapter requires 'anthropic'. Install with: pip install anthropic"
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def _call(self, prompt: str) -> str:
        import anthropic
        response = self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
