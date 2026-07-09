"""
classifier/action_classifier.py — Determine next message action via a rule table.

Single responsibility: decide WHAT to send next (MSG2/SEG1/SEG2/WAIT/NONE).

REGLA DE DETERMINISMO: 100% determinístico. Sin LLM. Sin probabilidades.
Sin heurísticas abiertas. Sin lenguaje natural en condiciones.
Mismo input → mismo output siempre, independientemente del modelo LLM posterior.

Rule table (ordered — first matching rule wins):
  A01  inventory.blocked                                             → NONE
  A02  stage == MEETING                                             → NONE
  A03  stage == MSG1_SENT  AND  last_msg == ""                     → WAIT
  A04  stage == MSG1_SENT  AND  last_msg != ""                     → MSG2
  A05  stage == MSG2_SENT  AND  dossier_sent == False              → WAIT
  A06  stage == DOSSIER_SENT  AND  days_since_dossier is None      → WAIT
  A07  stage == DOSSIER_SENT  AND  days < SEG1_WAIT_DAYS           → WAIT
  A08  stage == DOSSIER_SENT  AND  days >= SEG1_WAIT_DAYS          → SEG1
  A09  stage == SEG1_SENT   AND  days_since_dossier is None        → WAIT
  A10  stage == SEG1_SENT   AND  days < SEG2_WAIT_DAYS             → WAIT
  A11  stage == SEG1_SENT   AND  days >= SEG2_WAIT_DAYS            → SEG2
  A12  stage == UNKNOWN                                             → WAIT
  A13  default                                                      → WAIT
"""
from ..schemas.analysis import AnalysisResult, Stage
from ..schemas.classification import Action, ActionClassification
from ..schemas.evidence import EvidenceInventory

# Timing constants (days). Named so they appear verbatim in traces.
_SEG1_WAIT_DAYS = 3   # 48-72h after dossier sent
_SEG2_WAIT_DAYS = 10  # ~7 days after SEG1 (3 dossier + 7 SEG1 buffer)


def classify_action(
    analysis: AnalysisResult,
    inventory: EvidenceInventory,
) -> ActionClassification:
    """
    Apply rule table. Return first matching ActionClassification.
    The reason field encodes the rule ID and exact conditions that fired.
    """

    # A01
    if inventory.blocked:
        return ActionClassification(
            action=Action.NONE,
            reason="[A01] inventory.blocked=True → sin evidencia REAL, pipeline bloqueada",
        )

    # A02
    if analysis.stage == Stage.MEETING:
        return ActionClassification(
            action=Action.NONE,
            reason="[A02] stage=MEETING → prospecto ya en reunión",
        )

    # A03
    if analysis.stage == Stage.MSG1_SENT and not analysis.last_prospect_message.strip():
        return ActionClassification(
            action=Action.WAIT,
            reason="[A03] stage=MSG1_SENT AND last_prospect_message='' → sin respuesta aún",
        )

    # A04
    if analysis.stage == Stage.MSG1_SENT and analysis.last_prospect_message.strip():
        return ActionClassification(
            action=Action.MSG2,
            reason="[A04] stage=MSG1_SENT AND last_prospect_message≠'' → prospecto respondió a MSG1",
        )

    # A05
    if analysis.stage == Stage.MSG2_SENT and not analysis.dossier_sent:
        return ActionClassification(
            action=Action.WAIT,
            reason="[A05] stage=MSG2_SENT AND dossier_sent=False → dossier pendiente de confirmación",
        )

    # A06
    if analysis.stage == Stage.DOSSIER_SENT and analysis.days_since_dossier is None:
        return ActionClassification(
            action=Action.WAIT,
            reason="[A06] stage=DOSSIER_SENT AND days_since_dossier=None → fecha de dossier desconocida",
        )

    # A07
    if (
        analysis.stage == Stage.DOSSIER_SENT
        and analysis.days_since_dossier is not None
        and analysis.days_since_dossier < _SEG1_WAIT_DAYS
    ):
        return ActionClassification(
            action=Action.WAIT,
            reason=(
                f"[A07] stage=DOSSIER_SENT AND days_since_dossier={analysis.days_since_dossier}"
                f" < {_SEG1_WAIT_DAYS} → ventana SEG1 (48-72h) no cumplida"
            ),
        )

    # A08
    if (
        analysis.stage == Stage.DOSSIER_SENT
        and analysis.days_since_dossier is not None
        and analysis.days_since_dossier >= _SEG1_WAIT_DAYS
    ):
        return ActionClassification(
            action=Action.SEG1,
            reason=(
                f"[A08] stage=DOSSIER_SENT AND days_since_dossier={analysis.days_since_dossier}"
                f" >= {_SEG1_WAIT_DAYS} → ventana SEG1 cumplida"
            ),
        )

    # A09
    if analysis.stage == Stage.SEG1_SENT and analysis.days_since_dossier is None:
        return ActionClassification(
            action=Action.WAIT,
            reason="[A09] stage=SEG1_SENT AND days_since_dossier=None → fecha de dossier desconocida",
        )

    # A10
    if (
        analysis.stage == Stage.SEG1_SENT
        and analysis.days_since_dossier is not None
        and analysis.days_since_dossier < _SEG2_WAIT_DAYS
    ):
        return ActionClassification(
            action=Action.WAIT,
            reason=(
                f"[A10] stage=SEG1_SENT AND days_since_dossier={analysis.days_since_dossier}"
                f" < {_SEG2_WAIT_DAYS} → ventana SEG2 no cumplida"
            ),
        )

    # A11
    if (
        analysis.stage == Stage.SEG1_SENT
        and analysis.days_since_dossier is not None
        and analysis.days_since_dossier >= _SEG2_WAIT_DAYS
    ):
        return ActionClassification(
            action=Action.SEG2,
            reason=(
                f"[A11] stage=SEG1_SENT AND days_since_dossier={analysis.days_since_dossier}"
                f" >= {_SEG2_WAIT_DAYS} → ventana SEG2 cumplida"
            ),
        )

    # A12
    if analysis.stage == Stage.UNKNOWN:
        return ActionClassification(
            action=Action.WAIT,
            reason="[A12] stage=UNKNOWN → posición en secuencia indeterminada",
        )

    # A13 — default (safe fallback, should never fire in normal operation)
    return ActionClassification(
        action=Action.WAIT,
        reason=f"[A13] default fallback — stage={analysis.stage.value}",
    )
