"""
evidence_engine/tagger.py — Tag every claim from AnalysisResult as REAL/INFERRED/UNKNOWN.

Single responsibility: classify what we know. No decisions. No blocking.
Each item in AnalysisResult becomes one or more Evidence objects.
"""
from typing import List

from ..schemas.analysis import AnalysisResult
from ..schemas.evidence import Evidence, EvidenceSource, EvidenceType


def tag(analysis: AnalysisResult) -> List[Evidence]:
    """
    Convert AnalysisResult into a flat list of tagged Evidence objects.

    REAL   = came from the conversation itself (verbatim or observable)
    INFERRED = derived from LinkedIn profile, .md file, or sector assumptions
    UNKNOWN = information we don't have
    """
    evidence: List[Evidence] = []
    _counter = [1]

    def _next_id() -> str:
        ev_id = f"EV{_counter[0]:03d}"
        _counter[0] += 1
        return ev_id

    # ── Exact quotes from prospect (REAL) ─────────────────────────────────────
    # Source: conversation — the prospect said these verbatim.
    # prospect_exact_words may contain short full messages and split sentences.
    seen_phrases: set = set()
    for phrase in analysis.prospect_exact_words:
        if phrase in seen_phrases:
            continue
        seen_phrases.add(phrase)
        evidence.append(Evidence(
            id=_next_id(),
            claim=phrase,
            source=EvidenceSource.CONVERSATION,
            type=EvidenceType.REAL,
            usable=True,
            exact_quote=phrase,
        ))

    # ── Behavioral evidence: dossier response (REAL) ──────────────────────────
    # Observable fact: the prospect took an action (replied after dossier).
    if analysis.responded_to_dossier:
        evidence.append(Evidence(
            id="EV_DOSSIER_RESP",
            claim="El prospecto respondió al dossier",
            source=EvidenceSource.CONVERSATION,
            type=EvidenceType.REAL,
            usable=True,
        ))

    # ── System facts: dossier was sent (REAL) ─────────────────────────────────
    # We know this from either the .md stage or the conversation text.
    if analysis.dossier_sent:
        evidence.append(Evidence(
            id="EV_DOSSIER_SENT",
            claim="El dossier fue enviado al prospecto",
            source=EvidenceSource.CONVERSATION,
            type=EvidenceType.REAL,
            usable=True,
        ))

    # ── Temporal fact: days since dossier (REAL) ──────────────────────────────
    if analysis.days_since_dossier is not None:
        evidence.append(Evidence(
            id="EV_DAYS_DOSSIER",
            claim=f"Han pasado {analysis.days_since_dossier} días desde el dossier",
            source=EvidenceSource.CONVERSATION,
            type=EvidenceType.REAL,
            usable=True,
        ))

    # ── Sector from profile (INFERRED) ────────────────────────────────────────
    # Came from LinkedIn profile via dataset/reader, not from the conversation.
    if analysis.sector:
        evidence.append(Evidence(
            id="EV_SECTOR",
            claim=f"Prospecto en sector: {analysis.sector}",
            source=EvidenceSource.PROFILE,
            type=EvidenceType.INFERRED,
            usable=False,
        ))

    # ── Seniority from profile (INFERRED) ─────────────────────────────────────
    evidence.append(Evidence(
        id="EV_SENIORITY",
        claim=f"Seniority: {analysis.seniority.value}",
        source=EvidenceSource.PROFILE,
        type=EvidenceType.INFERRED,
        usable=False,
    ))

    # ── Previous MSG2 angle from .md (INFERRED) ───────────────────────────────
    # Stored in the .md file, not said by the prospect in this conversation.
    if analysis.previous_msg2_angle:
        evidence.append(Evidence(
            id="EV_MSG2_ANGLE",
            claim=f"Ángulo MSG2 previo: {analysis.previous_msg2_angle}",
            source=EvidenceSource.PROFILE,
            type=EvidenceType.INFERRED,
            usable=False,
        ))

    return evidence
