"""
strategy/strategy_builder.py — Produce a single StrategyDecision from all prior outputs.

Single responsibility: combine AnalysisResult + EvidenceInventory +
ActionClassification + StrategyClassification into ONE StrategyDecision.

This is the ÚNICO módulo autorizado a combinar los cuatro inputs anteriores.
Toda decisión comercial sale de aquí. No hay lógica distribuida.

What this module decides:
  - unique_objective    (the ONE goal for this message)
  - opening_angle       (from REAL evidence only)
  - mention_hint        (introduce Hint in this message?)
  - mention_dossier     (reference the dossier?)
  - propose_meeting     (include meeting CTA?)
  - cta                 (what type of CTA and suggested phrase)
  - personal_win        (what the PROSPECT gains as a person)
  - reference_client    (which Hint client to cite for this sector)
  - rotation            (angle rotation for SEG1/SEG2)
  - conversation_mode   (NORMAL or RECUPERACION)
  - bubbles             (message structure)
  - meeting_justification (mandatory text when propose_meeting=True)
"""
import json
from pathlib import Path
from typing import Optional

from ..schemas.analysis import AnalysisResult, Engagement
from ..schemas.classification import Action, ActionClassification, StrategyType, StrategyClassification
from ..schemas.evidence import EvidenceInventory
from ..schemas.strategy import (
    StrategyDecision, Bubble, CTADecision, ConversationMode,
)
from .rotation_engine import rotate
from .win_selector import select_win

# Config files consumed by this module
_SENIORITY_CFG = json.loads(
    (Path(__file__).parent.parent / "config" / "seniority.json").read_text(encoding="utf-8")
)
_SECTORS_CFG = json.loads(
    (Path(__file__).parent.parent / "config" / "sectors.json").read_text(encoding="utf-8")
)

_DOSSIER_CTA_PHRASE = (
    "Te puedo enviar un dossier breve por acá si no es mucha molestia, "
    "o me indicarías a quién se lo puedo mandar?"
)


def build(
    analysis: AnalysisResult,
    inventory: EvidenceInventory,
    action_cl: ActionClassification,
    strategy_cl: StrategyClassification,
) -> StrategyDecision:
    """
    Combine all prior module outputs into a single StrategyDecision.
    This is the only module that reads from all four inputs simultaneously.
    """
    # ── Blocked / no message ──────────────────────────────────────────────────
    if inventory.blocked or action_cl.action in (Action.WAIT, Action.NONE):
        return StrategyDecision(
            unique_objective="N/A",
            opening_angle=None,
            opening_angle_source="N/A",
            mention_hint=False,
            mention_dossier=False,
            propose_meeting=False,
            cta=CTADecision(allowed=False),
            personal_win=None,
            reference_client=None,
            rotation_applied=False,
            previous_angle=None,
            new_angle=None,
            conversation_mode=ConversationMode.NORMAL,
            blocked=True,
            block_reason=(
                inventory.block_reason
                if inventory.blocked
                else f"action={action_cl.action.value} — no hay mensaje a generar"
            ),
        )

    # ── Shared computations (run once, used below) ────────────────────────────
    opening_text     = _get_opening_text(inventory)
    personal_win     = select_win(analysis.seniority, analysis.engagement)
    reference_client = _get_reference_client(analysis.sector)
    conv_mode        = _detect_conversation_mode(analysis, action_cl)

    # Rotation applies only when we are past the dossier
    rotation_applied, new_angle, previous_angle = False, None, analysis.previous_msg2_angle
    if action_cl.action in (Action.SEG1, Action.SEG2):
        rotation_applied, new_angle = rotate(previous_angle)

    # ── Dispatch per action ───────────────────────────────────────────────────
    if action_cl.action == Action.MSG2:
        return _build_msg2(
            analysis, strategy_cl, opening_text,
            personal_win, reference_client, conv_mode,
            previous_angle, new_angle, rotation_applied,
        )

    if action_cl.action == Action.SEG1:
        return _build_seg1(
            analysis, strategy_cl, opening_text,
            personal_win, reference_client, conv_mode,
            previous_angle, new_angle, rotation_applied,
        )

    # SEG2
    return _build_seg2(
        analysis, strategy_cl, opening_text,
        personal_win, reference_client, conv_mode,
        previous_angle, new_angle, rotation_applied,
    )


# ── MSG2 ─────────────────────────────────────────────────────────────────────

def _build_msg2(
    analysis: AnalysisResult,
    strategy_cl: StrategyClassification,
    opening_text: Optional[str],
    personal_win: Optional[str],
    reference_client: Optional[str],
    conv_mode: ConversationMode,
    previous_angle: Optional[str],
    new_angle: Optional[str],
    rotation_applied: bool,
) -> StrategyDecision:
    return StrategyDecision(
        unique_objective="Presentar Hint y conseguir permiso para enviar dossier",
        opening_angle=opening_text,
        opening_angle_source="REAL",
        mention_hint=True,
        mention_dossier=True,
        propose_meeting=False,
        cta=CTADecision(
            allowed=True,
            type="DOSSIER",
            suggested_phrase=_DOSSIER_CTA_PHRASE,
        ),
        personal_win=personal_win,
        reference_client=reference_client,
        rotation_applied=False,
        previous_angle=previous_angle,
        new_angle=None,
        conversation_mode=conv_mode,
        bubbles=[
            Bubble(id="B1", objective="Conectar con la respuesta del prospecto. Máx 2 líneas. Citar sus palabras exactas."),
            Bubble(id="B2", objective="Aportar UNA idea o hacer UNA pregunta específica a su realidad. Máx 2 líneas."),
            Bubble(id="B3", objective="Presentar Hint en una oración: qué hacemos + con quién trabajamos + por qué le escribimos."),
            Bubble(id="B4", objective="Explicar qué contiene el dossier + pedir permiso con la frase fija del CTA."),
        ],
    )


# ── SEG1 ─────────────────────────────────────────────────────────────────────

def _build_seg1(
    analysis: AnalysisResult,
    strategy_cl: StrategyClassification,
    opening_text: Optional[str],
    personal_win: Optional[str],
    reference_client: Optional[str],
    conv_mode: ConversationMode,
    previous_angle: Optional[str],
    new_angle: Optional[str],
    rotation_applied: bool,
) -> StrategyDecision:
    # Objective depends on engagement level and conversation mode
    if conv_mode == ConversationMode.RECUPERACION:
        objective = "Recuperar vínculo con prospecto que mostró alto interés pero no respondió al dossier"
    elif analysis.engagement == Engagement.HIGH:
        objective = "Proponer reunión directamente con ángulo rotado"
    elif analysis.engagement == Engagement.MEDIUM:
        objective = "Reabrir conversación con ángulo nuevo, sin presionar"
    else:
        objective = "Hacer seguimiento breve y sin presión. Sin mencionar dossier ni reunión."

    # Meeting proposal: only HIGH engagement + non-EXPLORATORIA strategy
    propose_meeting = (
        analysis.engagement == Engagement.HIGH
        and strategy_cl.strategy in (StrategyType.CONSULTIVA, StrategyType.ENTRE_PARES)
        and conv_mode != ConversationMode.RECUPERACION
    )

    meeting_justification = (
        _get_meeting_justification(analysis.seniority.value)
        if propose_meeting else None
    )

    cta = (
        CTADecision(
            allowed=True,
            type=strategy_cl.strategy.value,
            suggested_phrase=_get_cta_phrase(analysis.seniority.value),
        )
        if propose_meeting
        else CTADecision(allowed=False)
    )

    bubbles = _seg1_bubbles(analysis.engagement, conv_mode, propose_meeting)

    return StrategyDecision(
        unique_objective=objective,
        opening_angle=new_angle or opening_text,
        opening_angle_source="REAL",
        mention_hint=analysis.engagement != Engagement.LOW,
        mention_dossier=False,
        propose_meeting=propose_meeting,
        cta=cta,
        personal_win=personal_win,
        reference_client=reference_client if analysis.engagement != Engagement.LOW else None,
        rotation_applied=rotation_applied,
        previous_angle=previous_angle,
        new_angle=new_angle,
        conversation_mode=conv_mode,
        bubbles=bubbles,
        meeting_justification=meeting_justification,
    )


# ── SEG2 ─────────────────────────────────────────────────────────────────────

def _build_seg2(
    analysis: AnalysisResult,
    strategy_cl: StrategyClassification,
    opening_text: Optional[str],
    personal_win: Optional[str],
    reference_client: Optional[str],
    conv_mode: ConversationMode,
    previous_angle: Optional[str],
    new_angle: Optional[str],
    rotation_applied: bool,
) -> StrategyDecision:
    meeting_justification = _get_meeting_justification(analysis.seniority.value)
    cta_phrase = _get_cta_phrase(analysis.seniority.value)

    return StrategyDecision(
        unique_objective="Proponer reunión directamente o cerrar el ciclo con elegancia",
        opening_angle=new_angle or opening_text,
        opening_angle_source="REAL",
        mention_hint=True,
        mention_dossier=False,
        propose_meeting=True,
        cta=CTADecision(
            allowed=True,
            type=strategy_cl.strategy.value,
            suggested_phrase=cta_phrase,
        ),
        personal_win=personal_win,
        reference_client=reference_client,
        rotation_applied=rotation_applied,
        previous_angle=previous_angle,
        new_angle=new_angle,
        conversation_mode=conv_mode,
        bubbles=[
            Bubble(
                id="B1",
                objective=(
                    "Proponer reunión con justificación clara para el prospecto. "
                    "Si no hay respuesta, cerrar el ciclo con elegancia."
                ),
            ),
        ],
        meeting_justification=meeting_justification,
    )


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_opening_text(inventory: EvidenceInventory) -> Optional[str]:
    """Get the text content of the opening evidence item."""
    if not inventory.opening_evidence_id:
        return None
    for ev in inventory.all_evidence:
        if ev.id == inventory.opening_evidence_id:
            return ev.exact_quote or ev.claim
    return None


def _get_reference_client(sector: str) -> Optional[str]:
    """Get the first Hint client for this sector."""
    entry = _SECTORS_CFG.get(sector) or _SECTORS_CFG.get("default", {})
    clients = entry.get("hint_clients", [])
    return clients[0] if clients else "Destiny Group"


def _detect_conversation_mode(
    analysis: AnalysisResult,
    action_cl: ActionClassification,
) -> ConversationMode:
    """
    Detect RECUPERACION: SEG1 + HIGH engagement + prospect never responded to dossier.
    This means they were enthusiastic in the conversation but disappeared after dossier.
    """
    if (
        action_cl.action == Action.SEG1
        and analysis.engagement == Engagement.HIGH
        and not analysis.responded_to_dossier
    ):
        return ConversationMode.RECUPERACION
    return ConversationMode.NORMAL


def _get_meeting_justification(seniority_value: str) -> Optional[str]:
    """Get meeting justification text from seniority config."""
    entry = _SENIORITY_CFG.get(seniority_value, {})
    return entry.get("meeting_justification")


def _get_cta_phrase(seniority_value: str) -> Optional[str]:
    """Get suggested CTA phrase from seniority config."""
    entry = _SENIORITY_CFG.get(seniority_value, {})
    return entry.get("cta_example")


def _seg1_bubbles(
    engagement: Engagement,
    conv_mode: ConversationMode,
    propose_meeting: bool,
) -> list:
    """Select bubble structure for SEG1 based on engagement and mode."""
    if conv_mode == ConversationMode.RECUPERACION:
        return [
            Bubble(id="B1", objective="Reconectar sin presionar. Partir desde un ángulo completamente nuevo."),
            Bubble(id="B2", objective="Aportar el win personal concreto para el prospecto, sin mencionar el dossier."),
        ]
    if engagement == Engagement.HIGH and propose_meeting:
        return [
            Bubble(id="B1", objective="Apertura desde el ángulo rotado o el win personal."),
            Bubble(id="B2", objective="Proponer reunión con la justificación específica para este seniority."),
        ]
    if engagement == Engagement.MEDIUM:
        return [
            Bubble(id="B1", objective="Apertura breve desde el ángulo rotado. Sin mencionar el dossier."),
            Bubble(id="B2", objective="Una pregunta o dato concreto del sector."),
        ]
    # LOW
    return [
        Bubble(id="B1", objective="Apertura muy breve. Sin mencionar el dossier, sin proponer reunión."),
    ]
