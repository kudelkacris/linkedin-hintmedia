"""
context_builder/builder.py — Translate StrategyDecision into LLMContext.

Single responsibility: build the minimal, deterministic LLMContext the LLM adapter
receives. No commercial decisions are made here. Every decision (CTA, rotation,
win personal, reference client, bubbles) is passed through from StrategyDecision.

What this module DOES:
  - allowed_topics    list of what the LLM may reference
  - forbidden_topics  list of what the LLM must not mention
  - allowed_claims    exact prospect quotes usable verbatim
  - forbidden_claims  inferred claims that must never appear as stated facts
  - tone              derived from engagement + strategy + conversation_mode
  - format_rules      non-negotiable formatting constraints

What this module does NOT:
  - Make strategy decisions
  - Change CTA content
  - Modify bubbles
  - Choose rotation or win personal
  - Add information not already in the inputs
"""
from typing import List

from ..schemas.analysis import AnalysisResult, Engagement
from ..schemas.classification import ActionClassification, StrategyClassification, StrategyType
from ..schemas.evidence import EvidenceInventory, EvidenceType
from ..schemas.strategy import StrategyDecision, ConversationMode
from ..schemas.context import LLMContext, FormatRules


def _first_name(full_name: str) -> str:
    """Extract first name only for greetings. 'Pedro Andrés Miranda' → 'Pedro'."""
    return full_name.strip().split()[0] if full_name.strip() else full_name


def build(
    analysis: AnalysisResult,
    inventory: EvidenceInventory,
    action_cl: ActionClassification,
    strategy_cl: StrategyClassification,
    decision: StrategyDecision,
    prospect_name: str = "",
) -> LLMContext:
    """
    Translate StrategyDecision into the LLMContext the LLM adapter receives.
    Only non-blocked decisions should reach this function.
    The caller (run.py) is responsible for stopping on decision.blocked.
    """
    return LLMContext(
        prospect_name=prospect_name,
        engagement=analysis.engagement.value,
        objective=decision.unique_objective,
        message_type=action_cl.action.value,
        opening_angle=decision.opening_angle,
        tone=_derive_tone(analysis, decision, strategy_cl),
        allowed_topics=_build_allowed_topics(analysis, decision),
        forbidden_topics=_build_forbidden_topics(analysis, decision),
        allowed_claims=_extract_allowed_claims(inventory),
        forbidden_claims=_extract_forbidden_claims(inventory),
        cta=decision.cta,
        personal_win=decision.personal_win,
        reference_client=decision.reference_client,
        conversation_mode=decision.conversation_mode.value,
        bubbles=decision.bubbles,
        format_rules=FormatRules(
            greeting=f"Buenas {_first_name(prospect_name)}!" if prospect_name else "Buenas!",
        ),
    )


# ── Allowed topics ────────────────────────────────────────────────────────────

def _build_allowed_topics(
    analysis: AnalysisResult,
    decision: StrategyDecision,
) -> List[str]:
    topics: List[str] = []

    if decision.opening_angle:
        topics.append(f"apertura desde: '{decision.opening_angle}'")

    if decision.mention_hint:
        note = f" (cliente de referencia: {decision.reference_client})" if decision.reference_client else ""
        topics.append(f"Hint Media — agencia omnicanal{note}")

    if decision.mention_dossier:
        topics.append("dossier — explicar qué contiene antes del CTA, nunca solo pedir permiso")

    if decision.propose_meeting and decision.meeting_justification:
        topics.append(f"reunión — justificación: {decision.meeting_justification}")

    if decision.personal_win:
        topics.append(f"win personal del prospecto: {decision.personal_win}")

    if decision.rotation_applied and decision.new_angle:
        topics.append(f"ángulo rotado obligatorio: {decision.new_angle}")

    if decision.conversation_mode == ConversationMode.RECUPERACION:
        topics.append("reconexión — abordar desde ángulo completamente nuevo")

    return topics


# ── Forbidden topics ──────────────────────────────────────────────────────────

def _build_forbidden_topics(
    analysis: AnalysisResult,
    decision: StrategyDecision,
) -> List[str]:
    topics: List[str] = [
        "abrir con el cargo o empresa del prospecto",
        "resumir el perfil del prospecto",
    ]

    if not decision.mention_hint:
        topics.append("mencionar Hint Media")

    if not decision.mention_dossier:
        topics.append("usar el dossier como apertura o gancho principal")

    if not decision.propose_meeting:
        topics.append("proponer reunión")

    if decision.previous_angle:
        topics.append(f"reutilizar el ángulo anterior: '{decision.previous_angle}'")

    if decision.conversation_mode == ConversationMode.RECUPERACION:
        topics.append("presionar para obtener respuesta")
        topics.append("mencionar que no respondió al dossier")

    if analysis.engagement == Engagement.LOW:
        topics.append("hacer más de una pregunta")
        topics.append("sonar urgente o insistente")

    return topics


# ── Claim extractors ──────────────────────────────────────────────────────────

def _extract_allowed_claims(inventory: EvidenceInventory) -> List[str]:
    """Only REAL evidence with an exact quote may appear verbatim in the draft."""
    return [
        ev.exact_quote
        for ev in inventory.all_evidence
        if ev.type == EvidenceType.REAL and ev.exact_quote is not None
    ]


def _extract_forbidden_claims(inventory: EvidenceInventory) -> List[str]:
    """INFERRED claims must never appear in the draft as stated facts."""
    return [
        ev.claim
        for ev in inventory.all_evidence
        if ev.type == EvidenceType.INFERRED
    ]


# ── Tone derivation ───────────────────────────────────────────────────────────

def _derive_tone(
    analysis: AnalysisResult,
    decision: StrategyDecision,
    strategy_cl: StrategyClassification,
) -> str:
    if decision.conversation_mode == ConversationMode.RECUPERACION:
        return "reconexión sin presión — ángulo completamente nuevo, sin mencionar el dossier"

    if decision.propose_meeting:
        if strategy_cl.strategy == StrategyType.ENTRE_PARES:
            return "entre pares — nunca pitch, nunca demo, intercambio de experiencias"
        return "consultivo y directo — mostrar valor concreto, proponer con justificación"

    if analysis.engagement == Engagement.HIGH:
        return "entusiasta pero con propósito — responder a su interés, avanzar"

    if analysis.engagement == Engagement.MEDIUM:
        return "conversacional y curioso — aportar valor, no presionar"

    return "muy breve y sin presión — sin mencionar dossier ni reunión"
