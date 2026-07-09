"""
classifier/strategy_classifier.py — Determine relational strategy via a rule table.

Single responsibility: decide HOW to position the message
(CONSULTIVA / ENTRE_PARES / EXPLORATORIA / RECUPERACION).

REGLA DE DETERMINISMO: 100% determinístico. Sin LLM. Sin probabilidades.
Lee seniority de AnalysisResult (ya normalizado por dataset/reader desde seniority.json).

Rule table (ordered — first matching rule wins):
  S01  action in (WAIT, NONE)                                 → EXPLORATORIA
  S02  action == SEG1 AND engagement == HIGH
       AND responded_to_dossier == False                      → RECUPERACION
  S03  seniority == CEO                                       → ENTRE_PARES
  S04  seniority == DIRECTOR                                  → ENTRE_PARES
  S05  seniority == MANAGER                                   → CONSULTIVA
  S06  seniority == SPECIALIST                                → CONSULTIVA
  S07  seniority == OTHER AND engagement == HIGH              → CONSULTIVA
  S08  seniority == OTHER                                     → EXPLORATORIA
  S09  default                                                → EXPLORATORIA
"""
from ..schemas.analysis import AnalysisResult, Seniority, Engagement
from ..schemas.classification import (
    Action, ActionClassification, StrategyType, StrategyClassification,
)


def classify_strategy(
    analysis: AnalysisResult,
    action_classification: ActionClassification,
) -> StrategyClassification:
    """
    Apply rule table. Return first matching StrategyClassification.
    The reason field encodes the rule ID and exact conditions that fired.
    Does NOT read config/seniority.json directly — the seniority mapping
    was already applied by dataset/reader.py (its responsibility).
    """
    action = action_classification.action

    # S01 — no message to send, strategy irrelevant
    if action in (Action.WAIT, Action.NONE):
        return StrategyClassification(
            strategy=StrategyType.EXPLORATORIA,
            reason=f"[S01] action={action.value} → no hay mensaje a enviar, estrategia no aplica",
        )

    # S02 — RECUPERACION: high engagement earlier but went cold (no dossier response)
    if (
        action == Action.SEG1
        and analysis.engagement == Engagement.HIGH
        and not analysis.responded_to_dossier
    ):
        return StrategyClassification(
            strategy=StrategyType.RECUPERACION,
            reason=(
                "[S02] action=SEG1 AND engagement=HIGH AND responded_to_dossier=False"
                " → prospecto entusiasmado que no respondió al dossier, recuperar vínculo"
            ),
        )

    # S03 — CEO → ENTRE_PARES
    if analysis.seniority == Seniority.CEO:
        return StrategyClassification(
            strategy=StrategyType.ENTRE_PARES,
            reason="[S03] seniority=CEO → conversación entre iguales sobre problema real de industria",
        )

    # S04 — DIRECTOR → ENTRE_PARES
    if analysis.seniority == Seniority.DIRECTOR:
        return StrategyClassification(
            strategy=StrategyType.ENTRE_PARES,
            reason="[S04] seniority=DIRECTOR → intercambio de perspectivas entre pares",
        )

    # S05 — MANAGER → CONSULTIVA
    if analysis.seniority == Seniority.MANAGER:
        return StrategyClassification(
            strategy=StrategyType.CONSULTIVA,
            reason="[S05] seniority=MANAGER → mostrar casos aplicables al trabajo inmediato",
        )

    # S06 — SPECIALIST → CONSULTIVA
    if analysis.seniority == Seniority.SPECIALIST:
        return StrategyClassification(
            strategy=StrategyType.CONSULTIVA,
            reason="[S06] seniority=SPECIALIST → resolver problema concreto con metodología probada",
        )

    # S07 — OTHER + HIGH → CONSULTIVA (engagement compensates for unknown seniority)
    if analysis.seniority == Seniority.OTHER and analysis.engagement == Engagement.HIGH:
        return StrategyClassification(
            strategy=StrategyType.CONSULTIVA,
            reason="[S07] seniority=OTHER AND engagement=HIGH → alto engagement justifica enfoque consultivo",
        )

    # S08 — OTHER (engagement not HIGH) → EXPLORATORIA
    if analysis.seniority == Seniority.OTHER:
        return StrategyClassification(
            strategy=StrategyType.EXPLORATORIA,
            reason=(
                f"[S08] seniority=OTHER AND engagement={analysis.engagement.value}"
                " → continuar conversación antes de comprometer estrategia"
            ),
        )

    # S09 — default fallback
    return StrategyClassification(
        strategy=StrategyType.EXPLORATORIA,
        reason=f"[S09] default fallback — seniority={analysis.seniority.value}",
    )
