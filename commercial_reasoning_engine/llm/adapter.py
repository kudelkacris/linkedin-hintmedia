"""
llm/adapter.py — Abstract LLM adapter.

Single responsibility: receive LLMContext, produce one draft string.
No commercial decisions. No strategy. No classification.

The adapter does exactly two things:
  1. build_prompt(context) → serializes LLMContext into a structured prompt
  2. _call(prompt) → sends it to the LLM (abstract — swap model here)

draft() = _call(build_prompt(context))
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..schemas.context import LLMContext
from ..schemas.strategy import ConversationMode


PROMPTS_DIR = Path(__file__).parent / "prompts"


class LLMAdapter(ABC):
    """
    Abstract base for all LLM backends.
    Subclasses implement only _call(). build_prompt() is shared.
    """

    def draft(self, context: LLMContext) -> str:
        """Build prompt, call LLM, return raw draft text."""
        prompt = self.build_prompt(context)
        return self._call(prompt)

    def build_prompt(self, context: LLMContext) -> str:
        """
        Serialize LLMContext into the full prompt the LLM receives.
        Template (static instructions) + context block (dynamic data).
        """
        template = self._load_template(context.message_type)
        context_block = self._serialize_context(context)
        return (
            f"{template}\n\n"
            f"---\n\n"
            f"{context_block}\n\n"
            f"Escribí el mensaje ahora. Solo el texto del mensaje. Sin etiquetas. Sin explicaciones."
        )

    @abstractmethod
    def _call(self, prompt: str) -> str:
        """Send prompt to the LLM. Return raw response text."""

    # ── Internals ──────────────────────────────────────────────────────────────

    @staticmethod
    def _load_template(message_type: str) -> str:
        name = message_type.lower()  # "MSG2" → "msg2"
        path = PROMPTS_DIR / f"{name}.txt"
        if not path.exists():
            raise FileNotFoundError(f"No prompt template for message type: {message_type}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _serialize_context(context: LLMContext) -> str:
        """Build human-readable context block from LLMContext."""
        lines: list[str] = []

        lines.append(f"PROSPECTO: {context.prospect_name or '(desconocido)'}")
        lines.append(f"TONO: {context.tone}")
        lines.append(f"OBJETIVO: {context.objective}")
        lines.append(f"MODO: {context.conversation_mode}")
        lines.append("")

        if context.opening_angle:
            lines.append("APERTURA OBLIGATORIA:")
            lines.append(f"  {context.opening_angle}")
            lines.append("")

        if context.bubbles:
            lines.append("ESTRUCTURA DE BURBUJAS:")
            for b in context.bubbles:
                lines.append(f"  {b.id}: {b.objective}")
            lines.append("")

        if context.allowed_topics:
            lines.append("PERMITIDO MENCIONAR:")
            for t in context.allowed_topics:
                lines.append(f"  - {t}")
            lines.append("")

        if context.forbidden_topics:
            lines.append("PROHIBIDO MENCIONAR:")
            for t in context.forbidden_topics:
                lines.append(f"  - {t}")
            lines.append("")

        if context.allowed_claims:
            lines.append("CITAS EXACTAS (podés usar estas palabras verbatim):")
            for c in context.allowed_claims:
                lines.append(f'  "{c}"')
            lines.append("")

        if context.forbidden_claims:
            lines.append("NO PRESENTAR COMO HECHOS (son inferencias, nunca hechos confirmados):")
            for c in context.forbidden_claims:
                lines.append(f'  "{c}"')
            lines.append("")

        if context.reference_client:
            lines.append(f"CLIENTE DE REFERENCIA: {context.reference_client}")
            lines.append("")

        if context.personal_win:
            lines.append("WIN PERSONAL DEL PROSPECTO:")
            lines.append(f"  {context.personal_win}")
            lines.append("")

        if context.cta.allowed and context.cta.suggested_phrase:
            lines.append("CTA:")
            lines.append(f"  {context.cta.suggested_phrase}")
            lines.append("")

        lines.append("FORMATO:")
        lines.append(f"  Saludo obligatorio: {context.format_rules.greeting}")
        if context.format_rules.no_long_dash:
            lines.append("  Sin guion largo (—). Usar punto o coma.")
        if context.format_rules.no_opening_punctuation:
            lines.append("  Sin ¡ ni ¿. Solo ! y ? de cierre.")
        lines.append(f"  Separador entre burbujas: salto simple (no línea en blanco).")
        lines.append(f"  Máx {context.format_rules.max_lines_per_bubble} líneas por burbuja.")

        return "\n".join(lines)
