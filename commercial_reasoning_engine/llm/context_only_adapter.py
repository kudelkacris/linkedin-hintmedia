"""
llm/context_only_adapter.py — No-API adapter for portable/offline use.

Instead of calling any LLM, this adapter:
  1. Writes the full prompt to a .txt file (one per conversation).
  2. Returns a placeholder draft so the pipeline continues normally.
  3. The Reviewer will see [PENDIENTE] and mark approved=False — expected.

Use cases:
  - Sprint Beta 3: generate all prompts, evaluate manually in any LLM.
  - CI / dry-run: validate Context Builder output without API costs.
  - Offline / air-gapped: export prompts, run LLM elsewhere, paste results back.

Usage:
    from commercial_reasoning_engine.llm.context_only_adapter import ContextOnlyAdapter
    from pathlib import Path

    adapter = ContextOnlyAdapter(output_dir=Path("sprint_beta3_output"))
    result = run(conversation, adapter=adapter, ...)
    # Prompt saved to sprint_beta3_output/<prospect_name>.txt
    # result.draft == "[PENDIENTE]"
"""
from pathlib import Path
from .adapter import LLMAdapter
from ..schemas.context import LLMContext

_PLACEHOLDER = "[PENDIENTE]"


class ContextOnlyAdapter(LLMAdapter):
    """
    Writes the full prompt to disk. Returns a placeholder draft.
    No API calls. No dependencies beyond the standard library.
    """

    def __init__(self, output_dir: Path | None = None):
        self._output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

    def draft(self, context: LLMContext) -> str:
        """Build prompt, save to file, return placeholder."""
        prompt = self.build_prompt(context)
        if self._output_dir:
            safe_name = (context.prospect_name or "prospect").replace(" ", "_").replace("/", "_")
            out_path = self._output_dir / f"{safe_name}.txt"
            out_path.write_text(prompt, encoding="utf-8")
        return _PLACEHOLDER

    def _call(self, prompt: str) -> str:
        return _PLACEHOLDER
