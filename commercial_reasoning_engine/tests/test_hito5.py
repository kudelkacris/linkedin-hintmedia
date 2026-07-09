"""
Tests for HITO 5 — rotation_engine, win_selector, strategy_builder.
No LLM. No external dependencies beyond config JSON files.
Run: python -m pytest commercial_reasoning_engine/tests/test_hito5.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.schemas.analysis import (
    AnalysisResult, Stage, Engagement, Seniority, Temperature,
)
from commercial_reasoning_engine.schemas.evidence import Evidence, EvidenceInventory, EvidenceType, EvidenceSource
from commercial_reasoning_engine.schemas.classification import (
    Action, ActionClassification, StrategyType, StrategyClassification,
)
from commercial_reasoning_engine.schemas.strategy import ConversationMode
from commercial_reasoning_engine.strategy.rotation_engine import rotate
from commercial_reasoning_engine.strategy.win_selector import select_win
from commercial_reasoning_engine.strategy.strategy_builder import build


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


def _inventory(quote: str = "Claro, decime.", blocked: bool = False) -> EvidenceInventory:
    if blocked:
        return EvidenceInventory(
            all_evidence=[], evidence_real_ids=[], evidence_inferred_ids=[],
            evidence_unknown_ids=[], opening_available=False,
            opening_evidence_id=None, blocked=True, block_reason="no evidence",
        )
    ev = Evidence(id="EV001", claim=quote, source=EvidenceSource.CONVERSATION,
                  type=EvidenceType.REAL, usable=True, exact_quote=quote)
    return EvidenceInventory(
        all_evidence=[ev], evidence_real_ids=["EV001"],
        evidence_inferred_ids=[], evidence_unknown_ids=[],
        opening_available=True, opening_evidence_id="EV001",
        blocked=False, block_reason=None,
    )


def _action(a: Action) -> ActionClassification:
    return ActionClassification(action=a, reason=f"[TEST] {a.value}")


def _strategy(s: StrategyType) -> StrategyClassification:
    return StrategyClassification(strategy=s, reason=f"[TEST] {s.value}")


# ─────────────────────────────────────────────────────────────────────────────
# ROTATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def test_rotate_exact_match():
    applied, new_angle = rotate("narrativa/comunicacion")
    assert applied is True
    assert new_angle == "eficiencia o ROI concreto"


def test_rotate_exact_match_branding():
    applied, new_angle = rotate("branding/identidad")
    assert applied is True
    assert new_angle == "posicionamiento personal del prospecto"


def test_rotate_substring_match():
    """'narrativa' matches key 'narrativa/comunicacion'."""
    applied, new_angle = rotate("narrativa")
    assert applied is True
    assert new_angle is not None


def test_rotate_no_angle_returns_false():
    applied, new_angle = rotate(None)
    assert applied is False
    assert new_angle is None


def test_rotate_empty_string_returns_false():
    applied, new_angle = rotate("")
    assert applied is False
    assert new_angle is None


def test_rotate_unknown_angle_uses_default():
    applied, new_angle = rotate("ángulo_que_no_existe_xyzzy")
    assert applied is True
    assert new_angle is not None  # uses default rotation


def test_rotate_paid_media():
    applied, new_angle = rotate("paid media/campañas")
    assert applied is True
    assert new_angle == "coherencia entre canales"


def test_rotate_voceria():
    applied, new_angle = rotate("vocería/CEO branding")
    assert applied is True
    assert "legibilidad" in new_angle or "persona" in new_angle


# ─────────────────────────────────────────────────────────────────────────────
# WIN SELECTOR
# ─────────────────────────────────────────────────────────────────────────────

def test_win_low_engagement_returns_none():
    result = select_win(Seniority.MANAGER, Engagement.LOW)
    assert result is None


def test_win_medium_engagement_returns_string():
    result = select_win(Seniority.MANAGER, Engagement.MEDIUM)
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 10


def test_win_high_engagement_returns_string():
    result = select_win(Seniority.DIRECTOR, Engagement.HIGH)
    assert result is not None
    assert isinstance(result, str)


def test_win_ceo_returns_relevant():
    result = select_win(Seniority.CEO, Engagement.HIGH)
    assert result is not None


def test_win_specialist_returns_string():
    result = select_win(Seniority.SPECIALIST, Engagement.MEDIUM)
    assert result is not None


def test_win_other_returns_string():
    result = select_win(Seniority.OTHER, Engagement.MEDIUM)
    assert result is not None


def test_win_deterministic():
    """Same seniority + engagement always returns the same win."""
    r1 = select_win(Seniority.MANAGER, Engagement.MEDIUM)
    r2 = select_win(Seniority.MANAGER, Engagement.MEDIUM)
    assert r1 == r2


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY BUILDER — blocked / wait
# ─────────────────────────────────────────────────────────────────────────────

def test_builder_blocked_inventory_returns_blocked():
    result = build(_analysis(), _inventory(blocked=True), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert result.blocked is True
    assert result.unique_objective == "N/A"
    assert result.propose_meeting is False
    assert result.mention_hint is False


def test_builder_wait_action_returns_blocked():
    result = build(_analysis(), _inventory(), _action(Action.WAIT), _strategy(StrategyType.CONSULTIVA))
    assert result.blocked is True
    assert "WAIT" in result.block_reason


def test_builder_none_action_returns_blocked():
    result = build(_analysis(), _inventory(), _action(Action.NONE), _strategy(StrategyType.CONSULTIVA))
    assert result.blocked is True


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY BUILDER — MSG2
# ─────────────────────────────────────────────────────────────────────────────

def test_builder_msg2_structure():
    result = build(_analysis(), _inventory(), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert not result.blocked
    assert result.mention_hint is True
    assert result.mention_dossier is True
    assert result.propose_meeting is False
    assert result.cta.allowed is True
    assert result.cta.type == "DOSSIER"
    assert result.cta.suggested_phrase is not None
    assert "dossier" in result.cta.suggested_phrase.lower()


def test_builder_msg2_has_4_bubbles():
    result = build(_analysis(), _inventory(), _action(Action.MSG2), _strategy(StrategyType.ENTRE_PARES))
    assert len(result.bubbles) == 4
    assert result.bubbles[0].id == "B1"
    assert result.bubbles[3].id == "B4"


def test_builder_msg2_no_rotation():
    result = build(_analysis(previous_msg2_angle="narrativa/comunicacion"), _inventory(), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert result.rotation_applied is False
    assert result.new_angle is None


def test_builder_msg2_opening_from_real_evidence():
    result = build(_analysis(), _inventory(quote="Claro, decime."), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert result.opening_angle == "Claro, decime."
    assert result.opening_angle_source == "REAL"


def test_builder_msg2_reference_client_from_sector():
    result = build(_analysis(sector="Energía"), _inventory(), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert result.reference_client in ("TGS", "Transener")


def test_builder_msg2_unknown_sector_uses_default_client():
    result = build(_analysis(sector="Sector Inexistente XYZ"), _inventory(), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert result.reference_client is not None


def test_builder_msg2_low_engagement_no_personal_win():
    result = build(_analysis(engagement=Engagement.LOW), _inventory(), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert result.personal_win is None


def test_builder_msg2_medium_engagement_has_personal_win():
    result = build(_analysis(engagement=Engagement.MEDIUM, seniority=Seniority.MANAGER), _inventory(), _action(Action.MSG2), _strategy(StrategyType.CONSULTIVA))
    assert result.personal_win is not None


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY BUILDER — SEG1
# ─────────────────────────────────────────────────────────────────────────────

def test_builder_seg1_low_engagement_1_bubble_no_meeting():
    analysis = _analysis(
        engagement=Engagement.LOW, dossier_sent=True,
        days_since_dossier=5, previous_msg2_angle="narrativa/comunicacion",
    )
    result = build(analysis, _inventory(), _action(Action.SEG1), _strategy(StrategyType.CONSULTIVA))
    assert not result.blocked
    assert result.propose_meeting is False
    assert result.mention_dossier is False
    assert len(result.bubbles) == 1


def test_builder_seg1_medium_engagement_2_bubbles_no_meeting():
    analysis = _analysis(
        engagement=Engagement.MEDIUM, dossier_sent=True,
        days_since_dossier=5, previous_msg2_angle="branding/identidad",
    )
    result = build(analysis, _inventory(), _action(Action.SEG1), _strategy(StrategyType.CONSULTIVA))
    assert result.propose_meeting is False
    assert len(result.bubbles) == 2


def test_builder_seg1_high_engagement_proposes_meeting():
    analysis = _analysis(
        engagement=Engagement.HIGH, dossier_sent=True,
        days_since_dossier=5, responded_to_dossier=True,
        previous_msg2_angle="contenido/alcance",
    )
    result = build(analysis, _inventory(), _action(Action.SEG1), _strategy(StrategyType.CONSULTIVA))
    assert result.propose_meeting is True
    assert result.cta.allowed is True
    assert result.meeting_justification is not None


def test_builder_seg1_applies_rotation():
    analysis = _analysis(
        engagement=Engagement.MEDIUM, dossier_sent=True,
        days_since_dossier=5, previous_msg2_angle="narrativa/comunicacion",
    )
    result = build(analysis, _inventory(), _action(Action.SEG1), _strategy(StrategyType.CONSULTIVA))
    assert result.rotation_applied is True
    assert result.new_angle == "eficiencia o ROI concreto"
    assert result.previous_angle == "narrativa/comunicacion"


def test_builder_seg1_no_prior_angle_rotation_false():
    analysis = _analysis(
        engagement=Engagement.MEDIUM, dossier_sent=True,
        days_since_dossier=5, previous_msg2_angle=None,
    )
    result = build(analysis, _inventory(), _action(Action.SEG1), _strategy(StrategyType.CONSULTIVA))
    assert result.rotation_applied is False
    assert result.new_angle is None


def test_builder_seg1_recuperacion_mode():
    """SEG1 + HIGH + not responded → RECUPERACION mode."""
    analysis = _analysis(
        engagement=Engagement.HIGH, dossier_sent=True,
        days_since_dossier=4, responded_to_dossier=False,
        previous_msg2_angle="narrativa/comunicacion",
    )
    result = build(analysis, _inventory(), _action(Action.SEG1), _strategy(StrategyType.CONSULTIVA))
    assert result.conversation_mode == ConversationMode.RECUPERACION
    assert result.propose_meeting is False  # RECUPERACION does NOT propose meeting
    assert len(result.bubbles) == 2


def test_builder_seg1_normal_mode_high_responded():
    """SEG1 + HIGH + responded_to_dossier=True → NORMAL mode."""
    analysis = _analysis(
        engagement=Engagement.HIGH, dossier_sent=True,
        days_since_dossier=5, responded_to_dossier=True,
        previous_msg2_angle=None,
    )
    result = build(analysis, _inventory(), _action(Action.SEG1), _strategy(StrategyType.CONSULTIVA))
    assert result.conversation_mode == ConversationMode.NORMAL


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY BUILDER — SEG2
# ─────────────────────────────────────────────────────────────────────────────

def test_builder_seg2_always_proposes_meeting():
    analysis = _analysis(
        engagement=Engagement.LOW, dossier_sent=True,
        days_since_dossier=12, previous_msg2_angle="paid media/campañas",
    )
    result = build(analysis, _inventory(), _action(Action.SEG2), _strategy(StrategyType.ENTRE_PARES))
    assert result.propose_meeting is True
    assert result.cta.allowed is True
    assert result.mention_hint is True
    assert result.mention_dossier is False


def test_builder_seg2_applies_rotation():
    analysis = _analysis(
        engagement=Engagement.LOW, dossier_sent=True,
        days_since_dossier=12, previous_msg2_angle="contenido/alcance",
    )
    result = build(analysis, _inventory(), _action(Action.SEG2), _strategy(StrategyType.CONSULTIVA))
    assert result.rotation_applied is True
    assert result.new_angle == "reducción de carga operativa"


def test_builder_seg2_1_bubble():
    result = build(_analysis(), _inventory(), _action(Action.SEG2), _strategy(StrategyType.ENTRE_PARES))
    assert len(result.bubbles) == 1


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY BUILDER — invariants
# ─────────────────────────────────────────────────────────────────────────────

def test_builder_opening_angle_source_always_real():
    """Non-blocked decisions always claim REAL as the source."""
    for action in (Action.MSG2, Action.SEG1, Action.SEG2):
        result = build(_analysis(), _inventory(), _action(action), _strategy(StrategyType.CONSULTIVA))
        if not result.blocked:
            assert result.opening_angle_source == "REAL", f"Failed for {action}"


def test_builder_mention_dossier_never_in_seg1_seg2():
    """Dossier already sent — never re-pitch it in SEG1/SEG2."""
    for action in (Action.SEG1, Action.SEG2):
        result = build(
            _analysis(dossier_sent=True, days_since_dossier=5),
            _inventory(), _action(action), _strategy(StrategyType.CONSULTIVA),
        )
        assert result.mention_dossier is False, f"mention_dossier=True in {action}"


def test_builder_deterministic():
    """Same inputs → identical StrategyDecision."""
    a = _analysis(engagement=Engagement.HIGH, dossier_sent=True, days_since_dossier=4, responded_to_dossier=False)
    inv = _inventory()
    ac = _action(Action.SEG1)
    sc = _strategy(StrategyType.ENTRE_PARES)
    r1 = build(a, inv, ac, sc)
    r2 = build(a, inv, ac, sc)
    assert r1.unique_objective == r2.unique_objective
    assert r1.conversation_mode == r2.conversation_mode
    assert r1.propose_meeting == r2.propose_meeting
    assert r1.new_angle == r2.new_angle
