"""
llm/claude_adapter.py — Claude API implementation of LLMAdapter.

Swap _MODEL or pass model= to use a different Claude version.
All commercial reasoning is done BEFORE this module runs.
This module only converts a structured prompt string into a text draft.
"""
import anthropic

from ..schemas.context import LLMContext
from .adapter import LLMAdapter


_MODEL = "claude-haiku-4-5-20251001"  # fast, cheap, sufficient for drafting
_MAX_TOKENS = 600


class ClaudeAdapter(LLMAdapter):
    def __init__(self, api_key: str | None = None, model: str = _MODEL):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def _call(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
