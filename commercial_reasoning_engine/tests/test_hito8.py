"""
HITO 8 — Reviewer tests.
No LLM calls. Pure string and logic checks.
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.schemas.context import LLMContext, FormatRules
from commercial_reasoning_engine.schemas.strategy import Bubble, CTADecision, ConversationMode
from commercial_reasoning_engine.schemas.review import ReviewResult, ReviewViolation
from commercial_reasoning_engine.reviewer.blocklist_checker import check as bl_check
from commercial_reasoning_engine.reviewer.perspective_checker import check as pv_check
from commercial_reasoning_engine.reviewer.evidence_checker import check as ev_check
from commercial_reasoning_engine.reviewer.reviewer import review


# ── Minimal context factory ────────────────────────────────────────────────────

def _ctx(forbidden_claims: list[str] | None = None) -> LLMContext:
    return LLMContext(
        prospect_name="Laura",
        engagement="MEDIUM",
        objective="pedir dossier",
        message_type="MSG2",
        opening_angle=None,
        tone="conversacional",
        allowed_topics=[],
        forbidden_topics=[],
        allowed_claims=[],
        forbidden_claims=forbidden_claims or [],
        cta=CTADecision(allowed=False),
        personal_win=None,
        reference_client=None,
        conversation_mode="NORMAL",
        bubbles=[],
        format_rules=FormatRules(greeting="Buenas Laura!"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCKLIST CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class TestBlocklistChecker:

    def test_clean_draft_passes(self):
        draft = "Buenas Laura!\nLo que compartiste sobre el equipo tiene mucho sentido.\n¿Cómo lo resolviste en contextos de alta presión?\nTe puedo mandar el dossier."
        assert bl_check(draft, _ctx()) == []

    def test_detects_gracias_por_la_apertura(self):
        draft = "Buenas Laura!\nGracias por la apertura."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_con_apertura_variant(self):
        draft = "Buenas Laura!\nRespondo con apertura a tu propuesta."
        v = bl_check(draft, _ctx())
        assert any("apertura" in v.description for v in v)

    def test_detects_por_eso_te_escribo(self):
        draft = "Por eso te escribo hoy."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_es_un_desafio_que_vemos_seguido(self):
        draft = "Es un desafío que vemos seguido en el sector."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_somos_una_agencia(self):
        draft = "Somos una agencia especializada."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_no_se_si_viste(self):
        draft = "No sé si viste lo que te mandé."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_retomo(self):
        draft = "Retomo lo que te comenté la semana pasada."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_quedo_atento(self):
        draft = "Quedo atento a tu respuesta."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_quedo_atenta(self):
        draft = "Quedo atenta."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_cualquier_duda(self):
        draft = "Cualquier duda, acá estoy."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_vi_que_sos(self):
        draft = "Vi que sos responsable del área."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_como_gerente_de(self):
        draft = "Como gerente de marketing, sabés que."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_me_comentabas(self):
        draft = "Me comentabas que el equipo tiene ese problema."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_queria_hacer_seguimiento(self):
        draft = "Quería hacer seguimiento de mi mensaje anterior."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_detects_no_queria_dejar_de_escribirte(self):
        draft = "No quería dejar de escribirte."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_case_insensitive(self):
        draft = "RETOMO lo que hablamos."
        v = bl_check(draft, _ctx())
        assert any(v.rule == "blocklist" for v in v)

    def test_multiple_violations_all_reported(self):
        draft = "Retomo. Quedo atenta. No sé si viste."
        v = bl_check(draft, _ctx())
        assert len(v) >= 3

    def test_violation_has_detected_fragment(self):
        draft = "Retomo lo que te escribí."
        v = bl_check(draft, _ctx())
        assert v[0].detected_fragment != ""

    def test_violation_rule_is_blocklist(self):
        draft = "Retomo."
        v = bl_check(draft, _ctx())
        assert all(x.rule == "blocklist" for x in v)


# ═══════════════════════════════════════════════════════════════════════════════
# PERSPECTIVE CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerspectiveChecker:

    def test_clean_draft_passes(self):
        draft = "Buenas Laura!\nLo que escribiste sobre el equipo tiene mucho sentido."
        assert pv_check(draft, _ctx()) == []

    def test_detects_en_hint_opener(self):
        draft = "Buenas Laura!\nEn Hint trabajamos con empresas de energía."
        v = pv_check(draft, _ctx())
        assert any(v.rule == "perspective" for v in v)

    def test_detects_trabajo_con_opener(self):
        draft = "Buenas Laura!\nTrabajo con equipos de comunicación en el sector."
        v = pv_check(draft, _ctx())
        assert any(v.rule == "perspective" for v in v)

    def test_detects_somos_opener(self):
        draft = "Buenas Laura!\nSomos una agencia que trabaja con líderes."
        v = pv_check(draft, _ctx())
        assert any(v.rule == "perspective" for v in v)

    def test_detects_nosotros_opener(self):
        draft = "Buenas Laura!\nNosotros nos especializamos en comunicación ejecutiva."
        v = pv_check(draft, _ctx())
        assert any(v.rule == "perspective" for v in v)

    def test_detects_hint_media_hace_opener(self):
        draft = "Buenas Laura!\nHint Media hace exactamente ese tipo de trabajo."
        v = pv_check(draft, _ctx())
        assert any(v.rule == "perspective" for v in v)

    def test_hint_in_b3_not_flagged(self):
        # Hint in B3 (not the first content line) is fine
        draft = (
            "Buenas Laura!\n"
            "Lo que describiste sobre el desafío de consistencia tiene mucho sentido.\n"
            "¿Cómo lo resolvieron en equipos distribuidos?\n"
            "En Hint trabajamos con empresas como TGS en ese tipo de comunicación.\n"
            "Te puedo mandar un dossier breve si no es mucha molestia."
        )
        v = pv_check(draft, _ctx())
        assert v == []

    def test_no_greeting_still_checks(self):
        # Draft without greeting: first line checked directly
        draft = "Lo que compartiste es muy relevante."
        assert pv_check(draft, _ctx()) == []

    def test_hint_opener_no_greeting(self):
        draft = "En Hint trabajamos con energía."
        v = pv_check(draft, _ctx())
        assert any(v.rule == "perspective" for v in v)

    def test_violation_has_fragment(self):
        draft = "Buenas Laura!\nTrabajo con equipos de comunicación."
        v = pv_check(draft, _ctx())
        assert v[0].detected_fragment != ""

    def test_empty_draft_no_crash(self):
        assert pv_check("", _ctx()) == []

    def test_only_greeting_no_crash(self):
        assert pv_check("Buenas Laura!", _ctx()) == []


# ═══════════════════════════════════════════════════════════════════════════════
# EVIDENCE CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvidenceChecker:

    def test_clean_draft_passes(self):
        ctx = _ctx(forbidden_claims=["Silvia busca expandirse internacionalmente"])
        draft = "Buenas Silvia!\nLo que describiste sobre liderazgo tiene sentido."
        assert ev_check(draft, ctx) == []

    def test_detects_trigram_from_forbidden_claim(self):
        ctx = _ctx(forbidden_claims=["el equipo no tiene agencia actual"])
        # Draft contains 3-word sequence from the claim
        draft = "Buenas Laura!\nSabemos que el equipo no tiene agencia para eso."
        v = ev_check(draft, ctx)
        assert any(v.rule == "evidence_leak" for v in v)

    def test_detects_partial_claim_leak(self):
        ctx = _ctx(forbidden_claims=["Laura lidera la transformación digital del grupo"])
        draft = "Buenas Laura!\nLidera la transformación digital con mucho foco."
        v = ev_check(draft, ctx)
        assert any(v.rule == "evidence_leak" for v in v)

    def test_multiple_claims_all_checked(self):
        ctx = _ctx(forbidden_claims=[
            "el prospecto no tiene agencia contratada",
            "la empresa está en crecimiento acelerado",
        ])
        draft = (
            "Buenas Laura!\n"
            "Entiendo que no tiene agencia contratada y que la empresa está en crecimiento."
        )
        v = ev_check(draft, ctx)
        assert len(v) >= 2

    def test_no_forbidden_claims_no_violations(self):
        ctx = _ctx(forbidden_claims=[])
        draft = "Buenas Laura!\nCualquier cosa que digas acá."
        assert ev_check(draft, ctx) == []

    def test_bigram_fallback_short_claim(self):
        ctx = _ctx(forbidden_claims=["maneja chile"])
        draft = "Sabemos que maneja Chile desde hace años."
        v = ev_check(draft, ctx)
        assert any(v.rule == "evidence_leak" for v in v)

    def test_unrelated_claim_no_violation(self):
        ctx = _ctx(forbidden_claims=["el prospecto tiene un conflicto con su jefe"])
        draft = "Buenas Laura!\nLo que escribiste sobre el equipo es muy claro."
        assert ev_check(draft, ctx) == []

    def test_violation_has_claim_in_description(self):
        ctx = _ctx(forbidden_claims=["el equipo no tiene agencia contratada"])
        draft = "Buenas!\nSabemos que el equipo no tiene agencia."
        v = ev_check(draft, ctx)
        assert "el equipo no tiene agencia contratada" in v[0].description

    def test_violation_rule_is_evidence_leak(self):
        ctx = _ctx(forbidden_claims=["el equipo no tiene agencia contratada"])
        draft = "Sabemos que el equipo no tiene agencia."
        v = ev_check(draft, ctx)
        assert all(x.rule == "evidence_leak" for x in v)

    def test_case_insensitive_matching(self):
        ctx = _ctx(forbidden_claims=["Laura Maneja Chile"])
        draft = "Buenas! laura maneja chile desde hace tiempo."
        v = ev_check(draft, ctx)
        assert any(v.rule == "evidence_leak" for v in v)


# ═══════════════════════════════════════════════════════════════════════════════
# REVIEWER (orchestrator)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReviewer:

    def _clean_draft(self):
        return (
            "Buenas Laura!\n"
            "Lo que describiste sobre la transformación tiene mucho sentido.\n"
            "¿Cómo lo están abordando en equipos distribuidos?\n"
            "Trabajo con líderes de energía en Hint Media, con clientes como TGS.\n"
            "Te puedo mandar el dossier por acá si no es mucha molestia."
        )

    def test_clean_draft_is_approved(self):
        result = review(self._clean_draft(), _ctx())
        assert result.approved is True

    def test_clean_draft_score_is_1(self):
        result = review(self._clean_draft(), _ctx())
        assert result.score == 1.0

    def test_clean_draft_has_final_message(self):
        draft = self._clean_draft()
        result = review(draft, _ctx())
        assert result.final_message == draft

    def test_blocklist_fail_rejected(self):
        draft = "Buenas Laura!\nRetomo lo que te escribí."
        result = review(draft, _ctx())
        assert result.approved is False

    def test_blocklist_fail_no_final_message(self):
        draft = "Buenas Laura!\nRetomo lo que te escribí."
        result = review(draft, _ctx())
        assert result.final_message is None

    def test_perspective_fail_rejected(self):
        draft = "Buenas Laura!\nEn Hint trabajamos con ese tipo de empresa."
        result = review(draft, _ctx())
        assert result.approved is False

    def test_evidence_fail_rejected(self):
        ctx = _ctx(forbidden_claims=["el equipo no tiene agencia contratada"])
        draft = "Buenas Laura!\nSé que el equipo no tiene agencia contratada."
        result = review(draft, ctx)
        assert result.approved is False

    def test_score_decreases_per_failed_checker(self):
        # Blocklist fail only → 2/3 checkers pass → score = 0.6667
        draft = "Buenas Laura!\nRetomo lo que te escribí.\nAlgo sobre el prospecto."
        result = review(draft, _ctx())
        assert result.score < 1.0
        assert result.score > 0.0

    def test_all_checkers_fail_score_is_0(self):
        ctx = _ctx(forbidden_claims=["el equipo no tiene agencia contratada"])
        draft = (
            "Buenas Laura!\n"
            "En Hint trabajamos con ese tipo de empresa. "
            "Retomo mi mensaje. "
            "El equipo no tiene agencia contratada para eso."
        )
        result = review(draft, ctx)
        assert result.score == 0.0

    def test_violations_list_populated_on_fail(self):
        draft = "Retomo. Quedo atento."
        result = review(draft, _ctx())
        assert len(result.violations) >= 2

    def test_violations_empty_on_pass(self):
        result = review(self._clean_draft(), _ctx())
        assert result.violations == []

    def test_returns_review_result_type(self):
        result = review(self._clean_draft(), _ctx())
        assert isinstance(result, ReviewResult)

    def test_violation_has_rule_field(self):
        draft = "Retomo."
        result = review(draft, _ctx())
        for v in result.violations:
            assert v.rule in ("blocklist", "perspective", "evidence_leak")

    def test_deterministic(self):
        draft = "Buenas Laura!\nRetomo lo que escribí."
        r1 = review(draft, _ctx())
        r2 = review(draft, _ctx())
        assert r1.approved == r2.approved
        assert r1.score == r2.score
