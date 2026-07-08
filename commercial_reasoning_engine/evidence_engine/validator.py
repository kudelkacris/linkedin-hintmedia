"""
evidence_engine/validator.py — Enforce usability rules and select opening evidence.

Single responsibility: guarantee that INFERRED/UNKNOWN items are never usable,
and select the best REAL evidence to open with.
"""
from typing import List, Optional

from ..schemas.evidence import Evidence, EvidenceType

# Opening evidence priority: prefer items with a verbatim quote (most concrete
# and human-sounding), then behavioral evidence, then temporal/system facts.
_OPENING_PRIORITY = ["EV_DOSSIER_RESP"]  # behavioral signals open well


def validate(evidence_list: List[Evidence]) -> List[Evidence]:
    """
    Enforce: INFERRED and UNKNOWN evidence is never usable.

    This is the only place where usable=False is enforced for INFERRED items.
    tagger.py already sets usable=False, but this ensures no tagger bug leaks through.
    """
    for ev in evidence_list:
        if ev.type in (EvidenceType.INFERRED, EvidenceType.UNKNOWN):
            ev.usable = False
    return evidence_list


def select_opening(evidence_list: List[Evidence]) -> Optional[str]:
    """
    Select the best REAL evidence item to open the message with.

    Priority:
    1. Exact quote from prospect (most concrete, verbatim)
    2. Behavioral evidence (dossier response — shows engagement)
    3. Any other usable REAL evidence
    Returns None if no REAL evidence exists.
    """
    usable = [ev for ev in evidence_list if ev.usable and ev.type == EvidenceType.REAL]

    if not usable:
        return None

    # 1. Prefer verbatim quotes
    with_quote = [ev for ev in usable if ev.exact_quote]
    if with_quote:
        return with_quote[0].id

    # 2. Behavioral signals (dossier response)
    behavioral = [ev for ev in usable if ev.id in _OPENING_PRIORITY]
    if behavioral:
        return behavioral[0].id

    # 3. Any usable REAL item
    return usable[0].id
