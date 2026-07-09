"""
Tests for HITO 3 — Evidence Engine (tagger, validator, engine).
No LLM calls. No external dependencies.
Run: python -m pytest commercial_reasoning_engine/tests/test_hito3.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.schemas.analysis import (
    AnalysisResult, Stage, Engagement, Seniority, Temperature,
)
from commercial_reasoning_engine.schemas.evidence import EvidenceType, EvidenceSource
from commercial_reasoning_engine.evidence_engine.tagger import tag
from commercial_reasoning_engine.evidence_engine.validator import validate, select_opening
from commercial_reasoning_engine.evidence_engine.engine import run


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_analysis(**overrides) -> AnalysisResult:
    defaults = dict(
        stage=Stage.MSG1_SENT,
        engagement=Engagement.LOW,
        sector="Farmacéutico",
        seniority=Seniority.MANAGER,
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
    defaults.update(overrides)
    return AnalysisResult(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# TAGGER TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_tagger_exact_quotes_are_real():
    analysis = _make_analysis(prospect_exact_words=["Claro, decime.", "Me interesa."])
    evidence = tag(analysis)
    quotes = [ev for ev in evidence if ev.exact_quote is not None]
    assert len(quotes) == 2
    for ev in quotes:
        assert ev.type == EvidenceType.REAL
        assert ev.usable is True
        assert ev.source == EvidenceSource.CONVERSATION


def test_tagger_sector_is_inferred():
    analysis = _make_analysis(sector="Energía")
    evidence = tag(analysis)
    sector_ev = next((ev for ev in evidence if ev.id == "EV_SECTOR"), None)
    assert sector_ev is not None
    assert sector_ev.type == EvidenceType.INFERRED
    assert sector_ev.usable is False


def test_tagger_seniority_is_inferred():
    analysis = _make_analysis()
    evidence = tag(analysis)
    seniority_ev = next((ev for ev in evidence if ev.id == "EV_SENIORITY"), None)
    assert seniority_ev is not None
    assert seniority_ev.type == EvidenceType.INFERRED
    assert seniority_ev.usable is False


def test_tagger_dossier_response_is_real():
    analysis = _make_analysis(responded_to_dossier=True, dossier_sent=True)
    evidence = tag(analysis)
    resp_ev = next((ev for ev in evidence if ev.id == "EV_DOSSIER_RESP"), None)
    assert resp_ev is not None
    assert resp_ev.type == EvidenceType.REAL
    assert resp_ev.usable is True


def test_tagger_dossier_sent_is_real():
    analysis = _make_analysis(dossier_sent=True)
    evidence = tag(analysis)
    sent_ev = next((ev for ev in evidence if ev.id == "EV_DOSSIER_SENT"), None)
    assert sent_ev is not None
    assert sent_ev.type == EvidenceType.REAL
    assert sent_ev.usable is True


def test_tagger_days_since_dossier_is_real():
    analysis = _make_analysis(dossier_sent=True, days_since_dossier=5)
    evidence = tag(analysis)
    days_ev = next((ev for ev in evidence if ev.id == "EV_DAYS_DOSSIER"), None)
    assert days_ev is not None
    assert days_ev.type == EvidenceType.REAL
    assert "5" in days_ev.claim


def test_tagger_msg2_angle_is_inferred():
    analysis = _make_analysis(previous_msg2_angle="narrativa/comunicación")
    evidence = tag(analysis)
    angle_ev = next((ev for ev in evidence if ev.id == "EV_MSG2_ANGLE"), None)
    assert angle_ev is not None
    assert angle_ev.type == EvidenceType.INFERRED
    assert angle_ev.usable is False


def test_tagger_no_duplicates_in_exact_words():
    analysis = _make_analysis(prospect_exact_words=["Claro.", "Claro.", "Me interesa."])
    evidence = tag(analysis)
    quotes = [ev for ev in evidence if ev.exact_quote is not None]
    texts = [ev.exact_quote for ev in quotes]
    assert len(texts) == len(set(texts)), "Duplicate exact quotes should be deduplicated"


def test_tagger_no_dossier_no_ev():
    """When dossier_sent=False, no EV_DOSSIER_SENT in evidence."""
    analysis = _make_analysis(dossier_sent=False)
    evidence = tag(analysis)
    assert not any(ev.id == "EV_DOSSIER_SENT" for ev in evidence)


def test_tagger_ids_are_unique():
    analysis = _make_analysis(
        prospect_exact_words=["A.", "B.", "C."],
        dossier_sent=True,
        responded_to_dossier=True,
        days_since_dossier=3,
        sector="Tecnología",
        previous_msg2_angle="alcance",
    )
    evidence = tag(analysis)
    ids = [ev.id for ev in evidence]
    assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_validator_enforces_inferred_not_usable():
    """Even if tagger accidentally marks INFERRED as usable, validator fixes it."""
    from commercial_reasoning_engine.schemas.evidence import Evidence
    evidence = [
        Evidence(id="EV001", claim="test", source=EvidenceSource.PROFILE,
                 type=EvidenceType.INFERRED, usable=True),  # wrong usable
    ]
    result = validate(evidence)
    assert result[0].usable is False


def test_validator_does_not_alter_real_usable():
    from commercial_reasoning_engine.schemas.evidence import Evidence
    evidence = [
        Evidence(id="EV001", claim="prospect said X", source=EvidenceSource.CONVERSATION,
                 type=EvidenceType.REAL, usable=True, exact_quote="X"),
    ]
    result = validate(evidence)
    assert result[0].usable is True


def test_select_opening_prefers_exact_quote():
    from commercial_reasoning_engine.schemas.evidence import Evidence
    evidence = [
        Evidence(id="EV_DOSSIER_SENT", claim="dossier sent", source=EvidenceSource.CONVERSATION,
                 type=EvidenceType.REAL, usable=True),
        Evidence(id="EV001", claim="Me interesa.", source=EvidenceSource.CONVERSATION,
                 type=EvidenceType.REAL, usable=True, exact_quote="Me interesa."),
    ]
    opening = select_opening(evidence)
    assert opening == "EV001"  # exact quote wins over behavioral


def test_select_opening_none_when_no_real():
    from commercial_reasoning_engine.schemas.evidence import Evidence
    evidence = [
        Evidence(id="EV_SECTOR", claim="sector: tech", source=EvidenceSource.PROFILE,
                 type=EvidenceType.INFERRED, usable=False),
    ]
    opening = select_opening(evidence)
    assert opening is None


def test_select_opening_falls_back_to_behavioral():
    from commercial_reasoning_engine.schemas.evidence import Evidence
    evidence = [
        Evidence(id="EV_DOSSIER_RESP", claim="respondió al dossier",
                 source=EvidenceSource.CONVERSATION, type=EvidenceType.REAL, usable=True),
        Evidence(id="EV_SECTOR", claim="sector: tech", source=EvidenceSource.PROFILE,
                 type=EvidenceType.INFERRED, usable=False),
    ]
    opening = select_opening(evidence)
    assert opening == "EV_DOSSIER_RESP"


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_engine_blocked_when_no_real_evidence():
    """No response, no dossier → no REAL evidence → blocked."""
    analysis = _make_analysis()
    inventory = run(analysis)
    assert inventory.blocked is True
    assert inventory.block_reason is not None
    assert len(inventory.evidence_real_ids) == 0


def test_engine_not_blocked_when_prospect_responded():
    analysis = _make_analysis(prospect_exact_words=["Claro, mandame el dossier."])
    inventory = run(analysis)
    assert inventory.blocked is False
    assert len(inventory.evidence_real_ids) > 0


def test_engine_not_blocked_when_dossier_sent():
    """SEG1 scenario: dossier sent, no response yet. Still has REAL evidence."""
    analysis = _make_analysis(dossier_sent=True, days_since_dossier=4)
    inventory = run(analysis)
    assert inventory.blocked is False
    assert "EV_DOSSIER_SENT" in inventory.evidence_real_ids


def test_engine_inferred_in_separate_list():
    analysis = _make_analysis(sector="Energía", seniority=Seniority.DIRECTOR)
    inventory = run(analysis)
    assert "EV_SECTOR" in inventory.evidence_inferred_ids
    assert "EV_SENIORITY" in inventory.evidence_inferred_ids


def test_engine_opening_set_when_real_exists():
    analysis = _make_analysis(prospect_exact_words=["Me interesa."])
    inventory = run(analysis)
    assert inventory.opening_available is True
    assert inventory.opening_evidence_id is not None


def test_engine_opening_none_when_blocked():
    analysis = _make_analysis()
    inventory = run(analysis)
    assert inventory.opening_available is False
    assert inventory.opening_evidence_id is None


def test_engine_all_evidence_contains_everything():
    analysis = _make_analysis(
        prospect_exact_words=["Dale."],
        dossier_sent=True,
        sector="Tecnología",
    )
    inventory = run(analysis)
    all_ids = [ev.id for ev in inventory.all_evidence]
    assert "EV_DOSSIER_SENT" in all_ids
    assert "EV_SECTOR" in all_ids


def test_engine_inferred_not_in_real_ids():
    """Inferred evidence must never appear in evidence_real_ids."""
    analysis = _make_analysis(
        sector="Energía",
        seniority=Seniority.CEO,
        dossier_sent=True,
    )
    inventory = run(analysis)
    for ev_id in inventory.evidence_real_ids:
        ev = next(e for e in inventory.all_evidence if e.id == ev_id)
        assert ev.type == EvidenceType.REAL, f"{ev_id} is {ev.type}, not REAL"


def test_engine_real_not_in_inferred_ids():
    """Real evidence must never appear in evidence_inferred_ids."""
    analysis = _make_analysis(
        prospect_exact_words=["Sí, enviame el dossier."],
        dossier_sent=True,
    )
    inventory = run(analysis)
    for ev_id in inventory.evidence_inferred_ids:
        ev = next(e for e in inventory.all_evidence if e.id == ev_id)
        assert ev.type == EvidenceType.INFERRED, f"{ev_id} is {ev.type}, not INFERRED"


def test_engine_full_scenario_with_response_and_dossier():
    """Full scenario: prospect responded with enthusiasm, dossier confirmed."""
    analysis = _make_analysis(
        stage=Stage.DOSSIER_SENT,
        engagement=Engagement.HIGH,
        sector="Farmacéutico",
        seniority=Seniority.DIRECTOR,
        is_decision_maker=True,
        last_prospect_message="Si claro podés enviármelo!",
        dossier_sent=True,
        days_since_dossier=2,
        responded_to_dossier=True,
        prospect_exact_words=["Si claro podés enviármelo!"],
        previous_msg2_angle="narrativa/comunicación",
        temperature=Temperature.HOT,
    )
    inventory = run(analysis)

    assert not inventory.blocked
    assert inventory.opening_available
    assert len(inventory.evidence_real_ids) >= 3  # quote + dossier resp + dossier sent + days
    assert "EV_MSG2_ANGLE" in inventory.evidence_inferred_ids
    assert "EV_SECTOR" in inventory.evidence_inferred_ids
    # Opening should be the exact quote
    opening_ev = next(ev for ev in inventory.all_evidence
                      if ev.id == inventory.opening_evidence_id)
    assert opening_ev.exact_quote is not None
