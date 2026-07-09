"""
HITO 7 — LLM Adapter tests.

Tests ONLY prompt construction. No real LLM calls.
ConcreteAdapter is a test double that returns a fixed string.
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.schemas.context import LLMContext, FormatRules
from commercial_reasoning_engine.schemas.strategy import Bubble, CTADecision, ConversationMode
from commercial_reasoning_engine.llm.adapter import LLMAdapter, PROMPTS_DIR


# ── Test double ───────────────────────────────────────────────────────────────

class ConcreteAdapter(LLMAdapter):
    """Minimal LLMAdapter for tests — _call() returns a fixed string."""

    FIXED_RESPONSE = "Buenas Test! Mensaje de prueba generado."

    def _call(self, prompt: str) -> str:
        return self.FIXED_RESPONSE


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_context(
    message_type: str = "MSG2",
    engagement: str = "MEDIUM",
    prospect_name: str = "Silvia",
    opening_angle: str | None = "Lo que compartis sobre liderazgo",
    mention_hint: bool = True,
    mention_dossier: bool = True,
    propose_meeting: bool = False,
    personal_win: str | None = "que su voz sea legible en el mercado",
    reference_client: str | None = "Destiny Group",
    conversation_mode: str = "NORMAL",
    allowed_topics: list | None = None,
    forbidden_topics: list | None = None,
    allowed_claims: list | None = None,
    forbidden_claims: list | None = None,
    bubbles: list | None = None,
    cta_allowed: bool = True,
    cta_phrase: str | None = "Te puedo enviar el dossier por aca.",
) -> LLMContext:
    if allowed_topics is None:
        allowed_topics = ["Hint Media", "dossier", "win personal del prospecto: liderazgo"]
    if forbidden_topics is None:
        forbidden_topics = ["cargo del prospecto", "proponer reunion"]
    if allowed_claims is None:
        allowed_claims = ["yo llevo anos liderando equipos"]
    if forbidden_claims is None:
        forbidden_claims = ["Silvia quiere expandirse internacionalmente"]
    if bubbles is None:
        bubbles = [
            Bubble("B1", "conectar con la respuesta del prospecto"),
            Bubble("B2", "hacer una pregunta sobre su desafio"),
            Bubble("B3", "presentar Hint Media"),
            Bubble("B4", "pedir permiso para el dossier"),
        ]
    return LLMContext(
        prospect_name=prospect_name,
        engagement=engagement,
        objective="profundizar y pedir dossier",
        message_type=message_type,
        opening_angle=opening_angle,
        tone="conversacional y curioso",
        allowed_topics=allowed_topics,
        forbidden_topics=forbidden_topics,
        allowed_claims=allowed_claims,
        forbidden_claims=forbidden_claims,
        cta=CTADecision(
            allowed=cta_allowed,
            type="CONSULTIVA",
            suggested_phrase=cta_phrase,
        ),
        personal_win=personal_win,
        reference_client=reference_client,
        conversation_mode=conversation_mode,
        bubbles=bubbles,
        format_rules=FormatRules(greeting="Buenas Silvia!"),
    )


ADAPTER = ConcreteAdapter()


# ── Template file existence ────────────────────────────────────────────────────

class TestTemplateFiles:
    def test_msg2_template_exists(self):
        assert (PROMPTS_DIR / "msg2.txt").exists()

    def test_seg1_template_exists(self):
        assert (PROMPTS_DIR / "seg1.txt").exists()

    def test_seg2_template_exists(self):
        assert (PROMPTS_DIR / "seg2.txt").exists()

    def test_msg2_template_non_empty(self):
        assert len((PROMPTS_DIR / "msg2.txt").read_text()) > 50

    def test_seg1_template_non_empty(self):
        assert len((PROMPTS_DIR / "seg1.txt").read_text()) > 50

    def test_seg2_template_non_empty(self):
        assert len((PROMPTS_DIR / "seg2.txt").read_text()) > 50

    def test_unknown_type_raises(self):
        ctx = _make_context(message_type="MSG1")
        with pytest.raises(FileNotFoundError):
            ADAPTER.build_prompt(ctx)


# ── Template selection ─────────────────────────────────────────────────────────

class TestTemplateSelection:
    def test_msg2_uses_msg2_template(self):
        ctx = _make_context(message_type="MSG2")
        prompt = ADAPTER.build_prompt(ctx)
        # Distinctive ASCII keyword only in msg2.txt
        assert "MSG2 de LinkedIn" in prompt

    def test_seg1_uses_seg1_template(self):
        ctx = _make_context(message_type="SEG1")
        prompt = ADAPTER.build_prompt(ctx)
        # Distinctive ASCII keyword only in seg1.txt
        assert "SEG1 de LinkedIn" in prompt

    def test_seg2_uses_seg2_template(self):
        ctx = _make_context(message_type="SEG2")
        prompt = ADAPTER.build_prompt(ctx)
        # Distinctive ASCII keyword only in seg2.txt
        assert "SEG2 de LinkedIn" in prompt


# ── Prospect data in prompt ────────────────────────────────────────────────────

class TestProspectData:
    def test_prospect_name_in_prompt(self):
        ctx = _make_context(prospect_name="Laura")
        prompt = ADAPTER.build_prompt(ctx)
        assert "Laura" in prompt

    def test_tone_in_prompt(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        assert "conversacional y curioso" in prompt

    def test_objective_in_prompt(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        assert "profundizar y pedir dossier" in prompt

    def test_engagement_not_required_but_mode_in_prompt(self):
        ctx = _make_context(conversation_mode="RECUPERACION")
        prompt = ADAPTER.build_prompt(ctx)
        assert "RECUPERACION" in prompt

    def test_empty_name_uses_fallback(self):
        ctx = _make_context(prospect_name="")
        prompt = ADAPTER.build_prompt(ctx)
        assert "desconocido" in prompt


# ── Topics in prompt ──────────────────────────────────────────────────────────

class TestTopics:
    def test_allowed_topics_in_prompt(self):
        ctx = _make_context(allowed_topics=["Hint Media", "dossier"])
        prompt = ADAPTER.build_prompt(ctx)
        assert "Hint Media" in prompt
        assert "dossier" in prompt

    def test_forbidden_topics_in_prompt(self):
        ctx = _make_context(forbidden_topics=["cargo del prospecto"])
        prompt = ADAPTER.build_prompt(ctx)
        assert "cargo del prospecto" in prompt

    def test_allowed_claims_in_prompt(self):
        ctx = _make_context(allowed_claims=["frase exacta del prospecto"])
        prompt = ADAPTER.build_prompt(ctx)
        assert "frase exacta del prospecto" in prompt

    def test_forbidden_claims_in_prompt(self):
        ctx = _make_context(forbidden_claims=["inferencia inventada"])
        prompt = ADAPTER.build_prompt(ctx)
        assert "inferencia inventada" in prompt

    def test_empty_allowed_claims_no_crash(self):
        ctx = _make_context(allowed_claims=[])
        prompt = ADAPTER.build_prompt(ctx)
        assert "CITAS EXACTAS" not in prompt  # section omitted when empty

    def test_empty_forbidden_claims_no_crash(self):
        ctx = _make_context(forbidden_claims=[])
        prompt = ADAPTER.build_prompt(ctx)
        assert "NO PRESENTAR COMO HECHOS" not in prompt  # section omitted when empty


# ── CTA in prompt ─────────────────────────────────────────────────────────────

class TestCTA:
    def test_cta_phrase_in_prompt_when_allowed(self):
        ctx = _make_context(cta_allowed=True, cta_phrase="Te puedo enviar el dossier.")
        prompt = ADAPTER.build_prompt(ctx)
        assert "Te puedo enviar el dossier." in prompt

    def test_cta_absent_when_not_allowed(self):
        ctx = _make_context(cta_allowed=False, cta_phrase=None)
        prompt = ADAPTER.build_prompt(ctx)
        assert "CTA:" not in prompt

    def test_cta_absent_when_no_phrase(self):
        ctx = _make_context(cta_allowed=True, cta_phrase=None)
        prompt = ADAPTER.build_prompt(ctx)
        assert "CTA:" not in prompt


# ── Optional fields ───────────────────────────────────────────────────────────

class TestOptionalFields:
    def test_personal_win_in_prompt(self):
        ctx = _make_context(personal_win="que su voz sea legible")
        prompt = ADAPTER.build_prompt(ctx)
        assert "que su voz sea legible" in prompt

    def test_personal_win_absent_when_none(self):
        ctx = _make_context(personal_win=None)
        prompt = ADAPTER.build_prompt(ctx)
        assert "WIN PERSONAL" not in prompt

    def test_reference_client_in_prompt(self):
        ctx = _make_context(reference_client="TGS")
        prompt = ADAPTER.build_prompt(ctx)
        assert "TGS" in prompt

    def test_reference_client_absent_when_none(self):
        ctx = _make_context(reference_client=None)
        prompt = ADAPTER.build_prompt(ctx)
        assert "CLIENTE DE REFERENCIA" not in prompt

    def test_opening_angle_in_prompt(self):
        ctx = _make_context(opening_angle="Lo que escribiste sobre ESG")
        prompt = ADAPTER.build_prompt(ctx)
        assert "Lo que escribiste sobre ESG" in prompt

    def test_opening_angle_absent_when_none(self):
        ctx = _make_context(opening_angle=None)
        prompt = ADAPTER.build_prompt(ctx)
        assert "APERTURA OBLIGATORIA" not in prompt


# ── Bubbles in prompt ─────────────────────────────────────────────────────────

class TestBubbles:
    def test_bubble_ids_in_prompt(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        assert "B1" in prompt
        assert "B2" in prompt
        assert "B3" in prompt
        assert "B4" in prompt

    def test_bubble_objectives_in_prompt(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        assert "conectar con la respuesta del prospecto" in prompt
        assert "presentar Hint Media" in prompt

    def test_no_bubbles_no_crash(self):
        ctx = _make_context(bubbles=[])
        prompt = ADAPTER.build_prompt(ctx)
        assert isinstance(prompt, str)
        assert "ESTRUCTURA" not in prompt


# ── Format rules in prompt ────────────────────────────────────────────────────

class TestFormatRules:
    def test_greeting_in_prompt(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        assert "Buenas Silvia!" in prompt

    def test_no_long_dash_rule_in_prompt(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        # The rule about long dash should appear in the prompt
        assert "guion largo" in prompt or "—" in prompt

    def test_no_opening_punctuation_rule_in_prompt(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        assert "¡" in prompt or "apertura" in prompt.lower()


# ── Template-specific content ─────────────────────────────────────────────────

class TestTemplateSpecificContent:
    def test_seg1_template_has_no_dossier_rule(self):
        seg1 = (PROMPTS_DIR / "seg1.txt").read_text()
        assert "dossier" in seg1.lower()
        assert "no mencionas el dossier" in seg1.lower()

    def test_seg1_template_has_retomo_in_blocklist(self):
        seg1 = (PROMPTS_DIR / "seg1.txt").read_text()
        assert "Retomo" in seg1

    def test_msg2_template_has_4_bubbles_rule(self):
        msg2 = (PROMPTS_DIR / "msg2.txt").read_text()
        assert "4 burbujas" in msg2.lower() or "cuatro burbujas" in msg2.lower()

    def test_msg2_template_has_blocklist(self):
        msg2 = (PROMPTS_DIR / "msg2.txt").read_text()
        assert "PROHIBIDAS" in msg2.upper() or "PROHIBIDA" in msg2.upper()

    def test_seg2_template_has_reunion_context(self):
        seg2 = (PROMPTS_DIR / "seg2.txt").read_text()
        assert "reunion" in seg2.lower()

    def test_seg2_template_has_quedo_atento_in_blocklist(self):
        seg2 = (PROMPTS_DIR / "seg2.txt").read_text()
        assert "Quedo atento" in seg2


# ── Adapter behavior ──────────────────────────────────────────────────────────

class TestAdapterBehavior:
    def test_build_prompt_returns_str(self):
        ctx = _make_context()
        result = ADAPTER.build_prompt(ctx)
        assert isinstance(result, str)

    def test_draft_returns_str(self):
        ctx = _make_context()
        result = ADAPTER.draft(ctx)
        assert isinstance(result, str)

    def test_draft_returns_fixed_response(self):
        ctx = _make_context()
        assert ADAPTER.draft(ctx) == ConcreteAdapter.FIXED_RESPONSE

    def test_draft_calls_call_with_prompt(self):
        """draft() must pass build_prompt() output to _call()."""
        captured = {}

        class CapturingAdapter(LLMAdapter):
            def _call(self, prompt: str) -> str:
                captured["prompt"] = prompt
                return "ok"

        a = CapturingAdapter()
        ctx = _make_context()
        expected_prompt = a.build_prompt(ctx)
        a.draft(ctx)
        assert captured["prompt"] == expected_prompt

    def test_deterministic(self):
        """Same context always produces same prompt."""
        ctx = _make_context()
        assert ADAPTER.build_prompt(ctx) == ADAPTER.build_prompt(ctx)

    def test_prompt_ends_with_write_instruction(self):
        ctx = _make_context()
        prompt = ADAPTER.build_prompt(ctx)
        assert "Escribí el mensaje ahora" in prompt
