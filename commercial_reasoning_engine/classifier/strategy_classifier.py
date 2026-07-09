"""
classifier/strategy_classifier.py — Determine relational strategy via a rule table.

Single responsibility: decide HOW to position the message
(CONSULTIVA / ENTRE_PARES / EXPLORATORIA).

REGLA DE DETERMINISMO: 100% determinístico. Sin LLM. Sin probabilidades.
Lee seniority de AnalysisResult (ya normalizado por dataset/reader desde seniority.json).

Note: RECUPERACION is NOT a strategy. It is a ConversationMode decided by
strategy_builder.py. See schemas/strategy.py → ConversationMode.

Rule table (ordered — first matching rule wins):
  S01  action in (WAIT, NONE)                      → EXPLORATORIA
  S02  seniority == CEO                            → ENTRE_PARES
  S03  seniority == DIRECTOR                       → ENTRE_PARES
  S04  seniority == MANAGER                        → CONSULTIVA
  S05  seniority == SPECIALIST                     → CONSULTIVA
  S06  seniority == OTHER AND engagement == HIGH   → CONSULTIVA
  S07  seniority == OTHER                          → EXPLORATORIA
  S08  default                                     → EXPLORATORIA
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

    # S02 — CEO → ENTRE_PARES
    if analysis.seniority == Seniority.CEO:
        return StrategyClassification(
            strategy=StrategyType.ENTRE_PARES,
            reason="[S02] seniority=CEO → conversación entre iguales sobre problema real de industria",
        )

    # S03 — DIRECTOR → ENTRE_PARES
    if analysis.seniority == Seniority.DIRECTOR:
        return StrategyClassification(
            strategy=StrategyType.ENTRE_PARES,
            reason="[S03] seniority=DIRECTOR → intercambio de perspectivas entre pares",
        )

    # S04 — MANAGER → CONSULTIVA
    if analysis.seniority == Seniority.MANAGER:
        return StrategyClassification(
            strategy=StrategyType.CONSULTIVA,
            reason="[S04] seniority=MANAGER → mostrar casos aplicables al trabajo inmediato",
        )

    # S05 — SPECIALIST → CONSULTIVA
    if analysis.seniority == Seniority.SPECIALIST:
        return StrategyClassification(
            strategy=StrategyType.CONSULTIVA,
            reason="[S05] seniority=SPECIALIST → resolver problema concreto con metodología probada",
        )

    # S06 — OTHER + HIGH → CONSULTIVA (engagement compensates for unknown seniority)
    if analysis.seniority == Seniority.OTHER and analysis.engagement == Engagement.HIGH:
        return StrategyClassification(
            strategy=StrategyType.CONSULTIVA,
            reason="[S06] seniority=OTHER AND engagement=HIGH → alto engagement justifica enfoque consultivo",
        )

    # S07 — OTHER (engagement not HIGH) → EXPLORATORIA
    if analysis.seniority == Seniority.OTHER:
        return StrategyClassification(
            strategy=StrategyType.EXPLORATORIA,
            reason=(
                f"[S07] seniority=OTHER AND engagement={analysis.engagement.value}"
                " → continuar conversación antes de comprometer estrategia"
            ),
        )

    # S08 — default fallback
    return StrategyClassification(
        strategy=StrategyType.EXPLORATORIA,
        reason=f"[S08] default fallback — seniority={analysis.seniority.value}",
    )
