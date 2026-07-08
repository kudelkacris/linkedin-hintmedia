"""
evidence_engine/engine.py — Produce EvidenceInventory from AnalysisResult.

Single responsibility: orchestrate tagger + validator → EvidenceInventory.
This is the ÚNICO PUNTO DE BLOQUEO for the pipeline:
if no REAL evidence exists, blocked=True and the pipeline stops.
"""
from ..schemas.analysis import AnalysisResult
from ..schemas.evidence import EvidenceInventory, EvidenceType
from .tagger import tag
from .validator import validate, select_opening

_NO_REAL_EVIDENCE_REASON = (
    "No hay evidencia REAL disponible. "
    "El prospecto no ha respondido ni ha habido interacción observable en la conversación. "
    "No se puede construir un mensaje sin evidencia concreta."
)


def run(analysis: AnalysisResult) -> EvidenceInventory:
    """
    Produce an EvidenceInventory from an AnalysisResult.

    Steps:
    1. tag()      — classify each observation as REAL/INFERRED/UNKNOWN
    2. validate() — enforce that INFERRED/UNKNOWN are usable=False
    3. select_opening() — pick the best REAL evidence to open with
    4. Apply blocking rule — if no REAL evidence → blocked=True

    Returns EvidenceInventory. Never raises. Blocking is communicated via
    the blocked/block_reason fields.
    """
    evidence_list = tag(analysis)
    evidence_list = validate(evidence_list)

    real_ids     = [ev.id for ev in evidence_list if ev.type == EvidenceType.REAL]
    inferred_ids = [ev.id for ev in evidence_list if ev.type == EvidenceType.INFERRED]
    unknown_ids  = [ev.id for ev in evidence_list if ev.type == EvidenceType.UNKNOWN]

    opening_id        = select_opening(evidence_list)
    opening_available = opening_id is not None

    blocked      = len(real_ids) == 0
    block_reason = _NO_REAL_EVIDENCE_REASON if blocked else None

    return EvidenceInventory(
        all_evidence=evidence_list,
        evidence_real_ids=real_ids,
        evidence_inferred_ids=inferred_ids,
        evidence_unknown_ids=unknown_ids,
        opening_available=opening_available,
        opening_evidence_id=opening_id,
        blocked=blocked,
        block_reason=block_reason,
    )
