"""
Tests for HITO 4 — Action Classifier + Strategy Classifier.
Every rule (A01-A13, S01-S09) has at least one test.
No LLM. No external dependencies.
Run: python -m pytest commercial_reasoning_engine/tests/test_hito4.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.schemas.analysis import (
    AnalysisResult, Stage, Engagement, Seniority, Temperature,
)
from commercial_reasoning_engine.schemas.evidence import EvidenceInventory
from commercial_reasoning_engine.schemas.classification import Action, StrategyType
from commercial_reasoning_engine.classifier.action_classifier import classify_action
from commercial_reasoning_engine.classifier.strategy_classifier import classify_strategy


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _analysis(**kw) -> AnalysisResult:
    defaults = dict(
        stage=Stage.MSG1_SENT,
        engagement=Engagement.LOW,
        sector="",
        seniority=Seniority.OTHER,
        is_decision_maker=False,
        last_prospect_message="",
        dossier_sent=False,
        days_since_dossier=None,
        days_since_seg1=None,
        days_since_seg2=None,
        responded_to_dossier=False,
        open_question=None,
        prospect_exact_words=[],
        previous_msg2_angle=None,
        temperature=Temperature.COLD,
    )
    defaults.update(kw)
    return AnalysisResult(**defaults)


def _inventory(blocked=False, real_ids=None) -> EvidenceInventory:
    return EvidenceInventory(
        all_evidence=[],
        evidence_real_ids=real_ids or ([] if blocked else ["EV001"]),
        evidence_inferred_ids=[],
        evidence_unknown_ids=[],
        opening_available=not blocked,
        opening_evidence_id=None if blocked else "EV001",
        blocked=blocked,
        block_reason="no evidence" if blocked else None,
    )


def _action_classification(action: Action):
    from commercial_reasoning_engine.schemas.classification import ActionClassification
    return ActionClassification(action=action, reason=f"[TEST] action={action.value}")


# ─────────────────────────────────────────────────────────────────────────────
# ACTION CLASSIFIER — one test per rule
# ─────────────────────────────────────────────────────────────────────────────

def test_A01_blocked_inventory_returns_none():
    """A01: blocked inventory → NONE regardless of stage."""
    analysis = _analysis(last_prospect_message="Claro, mandame el dossier.")
    inv = _inventory(blocked=True)
    result = classify_action(analysis, inv)
    assert result.action == Action.NONE
    assert "[A01]" in result.reason


def test_A02_meeting_stage_returns_none():
    """A02: stage=MEETING → NONE."""
    analysis = _analysis(stage=Stage.MEETING)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.NONE
    assert "[A02]" in result.reason


def test_A03_msg1_no_response_returns_wait():
    """A03: MSG1_SENT + empty last_message → WAIT."""
    analysis = _analysis(stage=Stage.MSG1_SENT, last_prospect_message="")
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A03]" in result.reason


def test_A03_whitespace_counts_as_no_response():
    """A03: whitespace-only last_message → WAIT (strip behavior)."""
    analysis = _analysis(stage=Stage.MSG1_SENT, last_prospect_message="   ")
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A03]" in result.reason


def test_A04_msg1_with_response_returns_msg2():
    """A04: MSG1_SENT + non-empty last_message → MSG2."""
    analysis = _analysis(stage=Stage.MSG1_SENT, last_prospect_message="Hola, claro decime.")
    result = classify_action(analysis, _inventory())
    assert result.action == Action.MSG2
    assert "[A04]" in result.reason


def test_A05_msg2_sent_no_dossier_returns_wait():
    """A05: MSG2_SENT + dossier_sent=False → WAIT."""
    analysis = _analysis(stage=Stage.MSG2_SENT, dossier_sent=False)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A05]" in result.reason


def test_A06_dossier_sent_no_date_returns_wait():
    """A06: DOSSIER_SENT + days=None → WAIT."""
    analysis = _analysis(stage=Stage.DOSSIER_SENT, dossier_sent=True, days_since_dossier=None)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A06]" in result.reason


def test_A07_dossier_sent_too_soon_returns_wait():
    """A07: DOSSIER_SENT + days < 3 → WAIT."""
    analysis = _analysis(stage=Stage.DOSSIER_SENT, dossier_sent=True, days_since_dossier=2)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A07]" in result.reason


def test_A07_boundary_day_2():
    """A07: exactly 2 days → still WAIT."""
    analysis = _analysis(stage=Stage.DOSSIER_SENT, dossier_sent=True, days_since_dossier=2)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT


def test_A08_dossier_sent_ready_returns_seg1():
    """A08: DOSSIER_SENT + days >= 3 → SEG1."""
    analysis = _analysis(stage=Stage.DOSSIER_SENT, dossier_sent=True, days_since_dossier=3)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.SEG1
    assert "[A08]" in result.reason


def test_A08_dossier_sent_week_later():
    """A08: 7 days since dossier → SEG1."""
    analysis = _analysis(stage=Stage.DOSSIER_SENT, dossier_sent=True, days_since_dossier=7)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.SEG1


def test_A09_seg1_sent_no_date_returns_wait():
    """A09: SEG1_SENT + days=None → WAIT."""
    analysis = _analysis(stage=Stage.SEG1_SENT, dossier_sent=True, days_since_dossier=None)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A09]" in result.reason


def test_A10_seg1_sent_too_soon_returns_wait():
    """A10: SEG1_SENT + days < 10 → WAIT."""
    analysis = _analysis(stage=Stage.SEG1_SENT, dossier_sent=True, days_since_dossier=7)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A10]" in result.reason


def test_A11_seg1_sent_ready_returns_seg2():
    """A11: SEG1_SENT + days >= 10 → SEG2."""
    analysis = _analysis(stage=Stage.SEG1_SENT, dossier_sent=True, days_since_dossier=10)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.SEG2
    assert "[A11]" in result.reason


def test_A12_unknown_stage_returns_wait():
    """A12: stage=UNKNOWN → WAIT."""
    analysis = _analysis(stage=Stage.UNKNOWN)
    result = classify_action(analysis, _inventory())
    assert result.action == Action.WAIT
    assert "[A12]" in result.reason


# ─────────────────────────────────────────────────────────────────────────────
# ACTION CLASSIFIER — determinism guarantee
# ─────────────────────────────────────────────────────────────────────────────

def test_determinism_same_input_same_output():
    """Same input always produces identical output (determinism rule)."""
    analysis = _analysis(stage=Stage.DOSSIER_SENT, dossier_sent=True, days_since_dossier=5)
    inv = _inventory()
    result1 = classify_action(analysis, inv)
    result2 = classify_action(analysis, inv)
    assert result1.action == result2.action
    assert result1.reason == result2.reason


def test_rule_id_always_in_reason():
    """Every outcome must include a rule ID in brackets."""
    cases = [
        _analysis(stage=Stage.MSG1_SENT, last_prospect_message=""),
        _analysis(stage=Stage.MSG1_SENT, last_prospect_message="Hola."),
        _analysis(stage=Stage.DOSSIER_SENT, dossier_sent=True, days_since_dossier=5),
        _analysis(stage=Stage.SEG1_SENT, dossier_sent=True, days_since_dossier=12),
        _analysis(stage=Stage.MEETING),
        _analysis(stage=Stage.UNKNOWN),
    ]
    inv = _inventory()
    for analysis in cases:
        result = classify_action(analysis, inv)
        assert result.reason.startswith("[A"), f"Missing rule ID in: {result.reason}"


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY CLASSIFIER — one test per rule
# ─────────────────────────────────────────────────────────────────────────────

def test_S01_wait_action_returns_exploratoria():
    """S01: action=WAIT → EXPLORATORIA."""
    analysis = _analysis()
    result = classify_strategy(analysis, _action_classification(Action.WAIT))
    assert result.strategy == StrategyType.EXPLORATORIA
    assert "[S01]" in result.reason


def test_S01_none_action_returns_exploratoria():
    """S01: action=NONE → EXPLORATORIA."""
    analysis = _analysis()
    result = classify_strategy(analysis, _action_classification(Action.NONE))
    assert result.strategy == StrategyType.EXPLORATORIA
    assert "[S01]" in result.reason


def test_S02_ceo_returns_entre_pares():
    """S02: seniority=CEO → ENTRE_PARES (RECUPERACION removed from strategy_classifier)."""
    analysis = _analysis(seniority=Seniority.CEO)
    result = classify_strategy(analysis, _action_classification(Action.SEG1))
    assert result.strategy == StrategyType.ENTRE_PARES
    assert "[S02]" in result.reason


def test_S03_director_returns_entre_pares():
    """S03: seniority=DIRECTOR → ENTRE_PARES."""
    analysis = _analysis(seniority=Seniority.DIRECTOR)
    result = classify_strategy(analysis, _action_classification(Action.MSG2))
    assert result.strategy == StrategyType.ENTRE_PARES
    assert "[S03]" in result.reason


def test_S04_manager_returns_consultiva():
    """S04: seniority=MANAGER → CONSULTIVA."""
    analysis = _analysis(seniority=Seniority.MANAGER)
    result = classify_strategy(analysis, _action_classification(Action.MSG2))
    assert result.strategy == StrategyType.CONSULTIVA
    assert "[S04]" in result.reason


def test_S05_specialist_returns_consultiva():
    """S05: seniority=SPECIALIST → CONSULTIVA."""
    analysis = _analysis(seniority=Seniority.SPECIALIST)
    result = classify_strategy(analysis, _action_classification(Action.MSG2))
    assert result.strategy == StrategyType.CONSULTIVA
    assert "[S05]" in result.reason


def test_S06_other_high_engagement_returns_consultiva():
    """S06: seniority=OTHER + engagement=HIGH → CONSULTIVA."""
    analysis = _analysis(seniority=Seniority.OTHER, engagement=Engagement.HIGH)
    result = classify_strategy(analysis, _action_classification(Action.MSG2))
    assert result.strategy == StrategyType.CONSULTIVA
    assert "[S06]" in result.reason


def test_S07_other_medium_engagement_returns_exploratoria():
    """S07: seniority=OTHER + engagement=MEDIUM → EXPLORATORIA."""
    analysis = _analysis(seniority=Seniority.OTHER, engagement=Engagement.MEDIUM)
    result = classify_strategy(analysis, _action_classification(Action.MSG2))
    assert result.strategy == StrategyType.EXPLORATORIA
    assert "[S07]" in result.reason


def test_S07_other_low_engagement_returns_exploratoria():
    """S07: seniority=OTHER + engagement=LOW → EXPLORATORIA."""
    analysis = _analysis(seniority=Seniority.OTHER, engagement=Engagement.LOW)
    result = classify_strategy(analysis, _action_classification(Action.MSG2))
    assert result.strategy == StrategyType.EXPLORATORIA
    assert "[S07]" in result.reason


def test_strategy_rule_id_always_in_reason():
    """Every strategy outcome must include a rule ID in brackets."""
    cases = [
        (_analysis(seniority=Seniority.CEO), Action.MSG2),
        (_analysis(seniority=Seniority.DIRECTOR), Action.SEG1),
        (_analysis(seniority=Seniority.MANAGER), Action.MSG2),
        (_analysis(seniority=Seniority.SPECIALIST), Action.MSG2),
        (_analysis(seniority=Seniority.OTHER, engagement=Engagement.HIGH), Action.MSG2),
        (_analysis(seniority=Seniority.OTHER, engagement=Engagement.LOW), Action.MSG2),
        (_analysis(), Action.WAIT),
    ]
    for analysis, action in cases:
        result = classify_strategy(analysis, _action_classification(action))
        assert result.reason.startswith("[S"), f"Missing rule ID in: {result.reason}"


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION — action + strategy together
# ─────────────────────────────────────────────────────────────────────────────

def test_integration_director_with_response():
    """Director responded to MSG1 → MSG2 + ENTRE_PARES."""
    analysis = _analysis(
        stage=Stage.MSG1_SENT,
        seniority=Seniority.DIRECTOR,
        last_prospect_message="Hola, claro decime.",
        engagement=Engagement.MEDIUM,
    )
    inv = _inventory()
    action_cl = classify_action(analysis, inv)
    strategy_cl = classify_strategy(analysis, action_cl)

    assert action_cl.action == Action.MSG2
    assert strategy_cl.strategy == StrategyType.ENTRE_PARES
    assert "[A04]" in action_cl.reason
    assert "[S03]" in strategy_cl.reason


def test_integration_manager_seg1_ready():
    """Manager, dossier sent 5 days ago, no response → SEG1 + CONSULTIVA."""
    analysis = _analysis(
        stage=Stage.DOSSIER_SENT,
        seniority=Seniority.MANAGER,
        dossier_sent=True,
        days_since_dossier=5,
        responded_to_dossier=False,
        engagement=Engagement.MEDIUM,
    )
    inv = _inventory()
    action_cl = classify_action(analysis, inv)
    strategy_cl = classify_strategy(analysis, action_cl)

    assert action_cl.action == Action.SEG1
    assert strategy_cl.strategy == StrategyType.CONSULTIVA


def test_integration_high_engagement_gone_cold():
    """HIGH engagement Manager didn't respond to dossier → SEG1 + CONSULTIVA.
    Note: RECUPERACION is now a ConversationMode decided by strategy_builder,
    not a StrategyType. The relational strategy stays CONSULTIVA for a Manager."""
    analysis = _analysis(
        stage=Stage.DOSSIER_SENT,
        seniority=Seniority.MANAGER,
        dossier_sent=True,
        days_since_dossier=4,
        responded_to_dossier=False,
        engagement=Engagement.HIGH,
    )
    inv = _inventory()
    action_cl = classify_action(analysis, inv)
    strategy_cl = classify_strategy(analysis, action_cl)

    assert action_cl.action == Action.SEG1
    assert strategy_cl.strategy == StrategyType.CONSULTIVA


def test_integration_blocked_produces_none_and_exploratoria():
    """Blocked inventory → NONE action → EXPLORATORIA strategy (no message)."""
    analysis = _analysis(stage=Stage.MSG1_SENT, last_prospect_message="Claro.")
    inv = _inventory(blocked=True)
    action_cl = classify_action(analysis, inv)
    strategy_cl = classify_strategy(analysis, action_cl)

    assert action_cl.action == Action.NONE
    assert strategy_cl.strategy == StrategyType.EXPLORATORIA


def test_integration_seg2_director():
    """Director, 12 days since dossier, SEG1 already sent → SEG2 + ENTRE_PARES."""
    analysis = _analysis(
        stage=Stage.SEG1_SENT,
        seniority=Seniority.DIRECTOR,
        dossier_sent=True,
        days_since_dossier=12,
        responded_to_dossier=False,
        engagement=Engagement.LOW,
    )
    inv = _inventory()
    action_cl = classify_action(analysis, inv)
    strategy_cl = classify_strategy(analysis, action_cl)

    assert action_cl.action == Action.SEG2
    assert strategy_cl.strategy == StrategyType.ENTRE_PARES
