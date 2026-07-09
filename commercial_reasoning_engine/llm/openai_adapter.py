"""
llm/openai_adapter.py — OpenAI-compatible adapter.

Covers: ChatGPT, Ollama, LM Studio, OpenRouter — any server that speaks the OpenAI API.

Usage:
    from commercial_reasoning_engine.llm.openai_adapter import OpenAICompatibleAdapter

    # ChatGPT
    adapter = OpenAICompatibleAdapter(api_key="sk-...", model="gpt-4o-mini")

    # Ollama (local, no key needed)
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="llama3",
    )

    # LM Studio (local)
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        model="mistral-7b-instruct",
    )

    # OpenRouter
    adapter = OpenAICompatibleAdapter(
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-or-...",
        model="anthropic/claude-haiku",
    )

Requires: pip install openai
"""
from .adapter import LLMAdapter

_DEFAULT_MAX_TOKENS = 600


class OpenAICompatibleAdapter(LLMAdapter):
    def __init__(
        self,
        api_key: str = "no-key",
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAICompatibleAdapter requires 'openai'. Install with: pip install openai"
            )
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._max_tokens = max_tokens

    def _call(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
