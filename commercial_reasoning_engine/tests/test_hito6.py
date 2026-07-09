"""
Tests for HITO 6 — Context Builder.
No LLM calls. No external dependencies.
Run: python -m pytest commercial_reasoning_engine/tests/test_hito6.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.schemas.analysis import (
    AnalysisResult, Stage, Engagement, Seniority, Temperature,
)
from commercial_reasoning_engine.schemas.evidence import (
    Evidence, EvidenceInventory, EvidenceType, EvidenceSource,
)
from commercial_reasoning_engine.schemas.classification import (
    Action, ActionClassification, StrategyType, StrategyClassification,
)
from commercial_reasoning_engine.schemas.strategy import (
    StrategyDecision, Bubble, CTADecision, ConversationMode,
)
from commercial_reasoning_engine.context_builder.builder import build


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _analysis(**kw) -> AnalysisResult:
    defaults = dict(
        stage=Stage.MSG1_SENT, engagement=Engagement.MEDIUM,
        sector="Farmacéutico", seniority=Seniority.MANAGER,
        is_decision_maker=False, last_prospect_message="Claro, decime.",
        dossier_sent=False, days_since_dossier=None,
        days_since_seg1=None, days_since_seg2=None,
        responded_to_dossier=False, open_question=None,
        prospect_exact_words=["Claro, decime."],
        previous_msg2_angle=None, temperature=Temperature.WARM,
    )
    defaults.update(kw)
    return AnalysisResult(**defaults)


def _inventory_with_quote(quote: str = "Claro, decime.") -> EvidenceInventory:
    ev = Evidence(
        id="EV001", claim=quote, source=EvidenceSource.CONVERSATION,
        type=EvidenceType.REAL, usable=True, exact_quote=quote,
    )
    inferred = Evidence(
        id="EV_SECTOR", claim="sector: Farmacéutico", source=EvidenceSource.PROFILE,
        type=EvidenceType.INFERRED, usable=False,
    )
    return EvidenceInventory(
        all_evidence=[ev, inferred],
        evidence_real_ids=["EV001"],
        evidence_inferred_ids=["EV_SECTOR"],
        evidence_unknown_ids=[],
        opening_available=True, opening_evidence_id="EV001",
        blocked=False, block_reason=None,
    )


def _inventory_no_quotes() -> EvidenceInventory:
    """Dossier sent, no prospect quotes."""
    sent = Evidence(
        id="EV_DOSSIER_SENT", claim="dossier enviado", source=EvidenceSource.CONVERSATION,
        type=EvidenceType.REAL, usable=True,
    )
    inferred = Evidence(
        id="EV_SENIORITY", claim="seniority: MANAGER inferido", source=EvidenceSource.PROFILE,
        type=EvidenceType.INFERRED, usable=False,
    )
    return EvidenceInventory(
        all_evidence=[sent, inferred],
        evidence_real_ids=["EV_DOSSIER_SENT"],
        evidence_inferred_ids=["EV_SENIORITY"],
        evidence_unknown_ids=[],
        opening_available=True, opening_evidence_id="EV_DOSSIER_SENT",
        blocked=False, block_reason=None,
    )


def _action(a: Action) -> ActionClassification:
    return ActionClassification(action=a, reason=f"[TEST] {a.value}")


def _strategy(s: StrategyType) -> StrategyClassification:
    return StrategyClassification(strategy=s, reason=f"[TEST] {s.value}")


def _decision_msg2(
    mention_hint=True, mention_dossier=True, propose_meeting=False,
    personal_win="reducir carga del equipo", reference_client="Libra Seguros",
    opening_angle="Claro, decime.", previous_angle=None, new_angle=None,
    rotation_applied=False, conv_mode=ConversationMode.NORMAL,
) -> StrategyDecision:
    return StrategyDecision(
        unique_objective="Presentar Hint y conseguir permiso para enviar dossier",
        opening_angle=opening_angle,
        opening_angle_source="REAL",
        mention_hint=mention_hint,
        mention_dossier=mention_dossier,
        propose_meeting=propose_meeting,
        cta=CTADecision(allowed=True, type="DOSSIER", suggested_phrase="Te puedo enviar un dossier..."),
        personal_win=personal_win,
        reference_client=reference_client,
        rotation_applied=rotation_applied,
        previous_angle=previous_angle,
        new_angle=new_angle,
        conversation_mode=conv_mode,
        bubbles=[Bubble(id="B1", objective="B1"), Bubble(id="B2", objective="B2"),
                 Bubble(id="B3", objective="B3"), Bubble(id="B4", objective="B4")],
        meeting_justification=None,
    )


def _decision_seg1(
    engagement=Engagement.MEDIUM, propose_meeting=False,
    rotation_applied=True, previous_angle="narrativa/comunicacion",
    new_angle="eficiencia o ROI concreto",
    conv_mode=ConversationMode.NORMAL,
    meeting_justification=None,
) -> StrategyDecision:
    return StrategyDecision(
        unique_objective="Reabrir conversación con ángulo nuevo",
        opening_angle=new_angle,
        opening_angle_source="REAL",
        mention_hint=True,
        mention_dossier=False,
        propose_meeting=propose_meeting,
        cta=CTADecision(allowed=propose_meeting, type="CONSULTIVA" if propose_meeting else None),
        personal_win="reducir carga del equipo",
        reference_client="Libra Seguros",
        rotation_applied=rotation_applied,
        previous_angle=previous_angle,
        new_angle=new_angle,
        conversation_mode=conv_mode,
        bubbles=[Bubble(id="B1", objective="B1"), Bubble(id="B2", objective="B2")],
        meeting_justification=meeting_justification,
    )


# ─────────────────────────────────────────────────────────────────────────────
# BASIC STRUCTURE
# ─────────────────────────────────────────────────────────────────────────────

def test_build_returns_llmcontext():
    from commercial_reasoning_engine.schemas.context import LLMContext
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(), "Carolina",
    )
    assert isinstance(result, LLMContext)


def test_prospect_name_in_greeting():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(), "Carolina",
    )
    assert result.prospect_name == "Carolina"
    assert "Carolina" in result.format_rules.greeting
    assert result.format_rules.greeting == "Buenas Carolina!"


def test_empty_prospect_name_fallback():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(), "",
    )
    assert result.format_rules.greeting == "Buenas!"


def test_message_type_from_action():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert result.message_type == "MSG2"


def test_message_type_seg1():
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), _decision_seg1(),
    )
    assert result.message_type == "SEG1"


def test_objective_from_decision():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert result.objective == "Presentar Hint y conseguir permiso para enviar dossier"


def test_bubbles_passed_through():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert len(result.bubbles) == 4
    assert result.bubbles[0].id == "B1"


def test_cta_passed_through():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert result.cta.allowed is True
    assert result.cta.type == "DOSSIER"


def test_personal_win_passed_through():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(personal_win="mi win"),
    )
    assert result.personal_win == "mi win"


def test_reference_client_passed_through():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(reference_client="TGS"),
    )
    assert result.reference_client == "TGS"


def test_opening_angle_passed_through():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(opening_angle="Me interesa mucho."),
    )
    assert result.opening_angle == "Me interesa mucho."


def test_conversation_mode_normal():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert result.conversation_mode == "NORMAL"


def test_conversation_mode_recuperacion():
    decision = _decision_seg1(conv_mode=ConversationMode.RECUPERACION)
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), decision,
    )
    assert result.conversation_mode == "RECUPERACION"


# ─────────────────────────────────────────────────────────────────────────────
# ALLOWED CLAIMS
# ─────────────────────────────────────────────────────────────────────────────

def test_allowed_claims_only_real_with_exact_quote():
    result = build(
        _analysis(), _inventory_with_quote("Claro, decime."), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert "Claro, decime." in result.allowed_claims


def test_allowed_claims_excludes_real_without_quote():
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), _decision_seg1(),
    )
    # EV_DOSSIER_SENT has no exact_quote — must not appear in allowed_claims
    assert len(result.allowed_claims) == 0


def test_allowed_claims_excludes_inferred():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    # EV_SECTOR is INFERRED — must not appear in allowed_claims
    assert "sector: Farmacéutico" not in result.allowed_claims


# ─────────────────────────────────────────────────────────────────────────────
# FORBIDDEN CLAIMS
# ─────────────────────────────────────────────────────────────────────────────

def test_forbidden_claims_contains_inferred():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert "sector: Farmacéutico" in result.forbidden_claims


def test_forbidden_claims_excludes_real():
    result = build(
        _analysis(), _inventory_with_quote("Me interesa."), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert "Me interesa." not in result.forbidden_claims


def test_forbidden_claims_has_seniority_when_inferred():
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), _decision_seg1(),
    )
    assert any("MANAGER" in c or "seniority" in c for c in result.forbidden_claims)


# ─────────────────────────────────────────────────────────────────────────────
# ALLOWED TOPICS
# ─────────────────────────────────────────────────────────────────────────────

def test_allowed_topics_includes_hint_when_true():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(mention_hint=True),
    )
    assert any("Hint Media" in t for t in result.allowed_topics)


def test_allowed_topics_includes_dossier_when_true():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(mention_dossier=True),
    )
    assert any("dossier" in t for t in result.allowed_topics)


def test_allowed_topics_includes_meeting_when_proposed():
    decision = _decision_seg1(
        propose_meeting=True,
        meeting_justification="perspectiva de cómo otros resuelven el mismo desafío",
    )
    result = build(
        _analysis(engagement=Engagement.HIGH), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.ENTRE_PARES), decision,
    )
    assert any("reunión" in t for t in result.allowed_topics)


def test_allowed_topics_includes_opening_angle():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(opening_angle="Claro, decime."),
    )
    assert any("Claro, decime." in t for t in result.allowed_topics)


def test_allowed_topics_includes_rotated_angle():
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA),
        _decision_seg1(rotation_applied=True, new_angle="eficiencia o ROI concreto"),
    )
    assert any("eficiencia o ROI concreto" in t for t in result.allowed_topics)


def test_allowed_topics_includes_personal_win():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(personal_win="no quedar expuesto ante su jefe"),
    )
    assert any("no quedar expuesto ante su jefe" in t for t in result.allowed_topics)


def test_allowed_topics_includes_reference_client():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(reference_client="TGS"),
    )
    assert any("TGS" in t for t in result.allowed_topics)


def test_allowed_topics_recuperacion_mode():
    decision = _decision_seg1(conv_mode=ConversationMode.RECUPERACION)
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), decision,
    )
    assert any("reconexión" in t for t in result.allowed_topics)


# ─────────────────────────────────────────────────────────────────────────────
# FORBIDDEN TOPICS
# ─────────────────────────────────────────────────────────────────────────────

def test_forbidden_topics_always_includes_cargo():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert any("cargo" in t for t in result.forbidden_topics)


def test_forbidden_topics_always_includes_resumir_perfil():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert any("perfil" in t for t in result.forbidden_topics)


def test_forbidden_topics_hint_when_false():
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA),
        _decision_seg1(),  # mention_hint=True default — test a LOW engagement where hint is False
    )
    # Build with mention_hint=False manually
    decision = _decision_msg2(mention_hint=False)
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), decision,
    )
    assert any("Hint Media" in t for t in result.forbidden_topics)


def test_forbidden_topics_dossier_when_false():
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), _decision_seg1(rotation_applied=False, new_angle=None),
    )
    assert any("dossier" in t for t in result.forbidden_topics)


def test_forbidden_topics_reunion_when_not_proposed():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(propose_meeting=False),
    )
    assert any("reunión" in t for t in result.forbidden_topics)


def test_forbidden_topics_previous_angle():
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA),
        _decision_seg1(previous_angle="branding/identidad"),
    )
    assert any("branding/identidad" in t for t in result.forbidden_topics)


def test_forbidden_topics_recuperacion_no_pressure():
    decision = _decision_seg1(conv_mode=ConversationMode.RECUPERACION)
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), decision,
    )
    assert any("presionar" in t for t in result.forbidden_topics)
    assert any("no respondió" in t for t in result.forbidden_topics)


def test_forbidden_topics_low_engagement_no_urgency():
    result = build(
        _analysis(engagement=Engagement.LOW), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), _decision_seg1(),
    )
    assert any("urgente" in t for t in result.forbidden_topics)
    assert any("pregunta" in t for t in result.forbidden_topics)


# ─────────────────────────────────────────────────────────────────────────────
# TONE
# ─────────────────────────────────────────────────────────────────────────────

def test_tone_recuperacion():
    decision = _decision_seg1(conv_mode=ConversationMode.RECUPERACION)
    result = build(
        _analysis(), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), decision,
    )
    assert "reconexión" in result.tone


def test_tone_entre_pares_with_meeting():
    decision = _decision_seg1(propose_meeting=True, meeting_justification="intercambio")
    result = build(
        _analysis(engagement=Engagement.HIGH), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.ENTRE_PARES), decision,
    )
    assert "entre pares" in result.tone


def test_tone_consultiva_with_meeting():
    decision = _decision_seg1(propose_meeting=True, meeting_justification="metodología")
    result = build(
        _analysis(engagement=Engagement.HIGH), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), decision,
    )
    assert "consultivo" in result.tone


def test_tone_high_no_meeting():
    result = build(
        _analysis(engagement=Engagement.HIGH), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(propose_meeting=False),
    )
    assert "entusiasta" in result.tone


def test_tone_medium():
    result = build(
        _analysis(engagement=Engagement.MEDIUM), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert "conversacional" in result.tone


def test_tone_low():
    result = build(
        _analysis(engagement=Engagement.LOW), _inventory_no_quotes(), _action(Action.SEG1),
        _strategy(StrategyType.CONSULTIVA), _decision_seg1(),
    )
    assert "sin presión" in result.tone


# ─────────────────────────────────────────────────────────────────────────────
# INVARIANTS
# ─────────────────────────────────────────────────────────────────────────────

def test_deterministic():
    """Same inputs → identical LLMContext."""
    a = _analysis()
    inv = _inventory_with_quote()
    ac = _action(Action.MSG2)
    sc = _strategy(StrategyType.CONSULTIVA)
    dec = _decision_msg2()
    r1 = build(a, inv, ac, sc, dec, "José")
    r2 = build(a, inv, ac, sc, dec, "José")
    assert r1.tone == r2.tone
    assert r1.allowed_topics == r2.allowed_topics
    assert r1.forbidden_topics == r2.forbidden_topics
    assert r1.allowed_claims == r2.allowed_claims
    assert r1.forbidden_claims == r2.forbidden_claims


def test_allowed_and_forbidden_do_not_overlap():
    """No topic can be simultaneously allowed and forbidden."""
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    for topic in result.allowed_topics:
        assert topic not in result.forbidden_topics, f"Overlap: '{topic}'"


def test_format_rules_no_long_dash():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert result.format_rules.no_long_dash is True


def test_format_rules_no_opening_punctuation():
    result = build(
        _analysis(), _inventory_with_quote(), _action(Action.MSG2),
        _strategy(StrategyType.CONSULTIVA), _decision_msg2(),
    )
    assert result.format_rules.no_opening_punctuation is True
