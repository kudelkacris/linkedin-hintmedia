"""
analyzer/analyzer.py — Extract observable facts from a conversation.

Single responsibility: produce AnalysisResult from ConversationInput + prospect_data.
No decisions. No inferences. No LLM calls. Only what can be observed.
"""
import re
from typing import Optional, List

from ..schemas.conversation import ConversationInput, Message
from ..schemas.analysis import (
    AnalysisResult, Stage, Engagement, Seniority, Temperature,
)

_EMOJI_RE = re.compile(
    r'[\U0001F300-\U0001F9FF\U00010000-\U0010FFFF]',
    re.UNICODE,
)

_DOSSIER_HINT_SIGNALS = [
    'dossier', 'te lo mando', 'te lo puedo mandar',
    'por acá si no es mucha molestia',
]
_DOSSIER_PROSPECT_CONFIRM = [
    'claro', 'ok', 'dale', 'sí', 'si', 'perfecto', 'adelante',
    'enviámelo', 'mandalo', 'mandame', 'por supuesto',
]

_SENIORITY_LOOKUP = {s.value: s for s in Seniority}


def analyze(conv: ConversationInput, prospect_data: Optional[dict] = None) -> AnalysisResult:
    """
    Extract all observable facts from a conversation.

    Only AnalysisResult fields that can be determined without inference are populated.
    Fields that require information not present in the conversation are set to None.
    """
    pd = prospect_data or {}

    hint_msgs    = [m for m in conv.messages if m.speaker == "hint"]
    prospect_msgs = [m for m in conv.messages if m.speaker == "prospect"]

    last_msg = prospect_msgs[-1].text if prospect_msgs else ""

    dossier_sent        = _detect_dossier_sent(hint_msgs, pd)
    responded_to_dossier = _detect_responded_to_dossier(prospect_msgs, hint_msgs, dossier_sent)
    engagement          = _score_engagement(prospect_msgs, dossier_sent, responded_to_dossier)
    stage               = _detect_stage(hint_msgs, prospect_msgs, dossier_sent, pd)
    temperature         = _score_temperature(engagement, stage)

    seniority_str = pd.get("cargo_seniority", "OTHER")
    seniority = _SENIORITY_LOOKUP.get(seniority_str, Seniority.OTHER)

    return AnalysisResult(
        stage=stage,
        engagement=engagement,
        sector=pd.get("sector") or "",
        seniority=seniority,
        is_decision_maker=seniority in (Seniority.CEO, Seniority.DIRECTOR),
        last_prospect_message=last_msg,
        dossier_sent=dossier_sent,
        days_since_dossier=pd.get("days_since_dossier"),
        responded_to_dossier=responded_to_dossier,
        open_question=_find_open_question(hint_msgs, prospect_msgs),
        prospect_exact_words=_extract_exact_words(prospect_msgs),
        previous_msg2_angle=pd.get("msg2_angle"),
        temperature=temperature,
    )


# ── Stage detection ───────────────────────────────────────────────────────────

def _detect_stage(
    hint_msgs: List[Message],
    prospect_msgs: List[Message],
    dossier_sent: bool,
    pd: dict,
) -> Stage:
    # .md file is authoritative when available
    if pd.get("stage"):
        stage_map = {
            "1": Stage.MSG1_SENT,
            "2": Stage.MSG2_SENT,
            "3": Stage.DOSSIER_SENT,
            "4": Stage.SEG1_SENT,
            "6": Stage.MEETING,
        }
        return stage_map.get(pd["stage"], Stage.UNKNOWN)

    # Infer from conversation structure
    if not prospect_msgs:
        return Stage.MSG1_SENT
    if dossier_sent:
        return Stage.DOSSIER_SENT
    if len(hint_msgs) >= 2:
        return Stage.MSG2_SENT
    return Stage.MSG1_SENT


# ── Dossier detection ─────────────────────────────────────────────────────────

def _detect_dossier_sent(hint_msgs: List[Message], pd: dict) -> bool:
    if pd.get("stage") in ("3", "4", "6"):
        return True
    return any(
        any(sig in m.text.lower() for sig in _DOSSIER_HINT_SIGNALS)
        for m in hint_msgs
    )


def _detect_responded_to_dossier(
    prospect_msgs: List[Message],
    hint_msgs: List[Message],
    dossier_sent: bool,
) -> bool:
    if not dossier_sent or not prospect_msgs:
        return False
    # Find index of last hint message that contained dossier signal
    dossier_hint_idx = -1
    for m in hint_msgs:
        if any(sig in m.text.lower() for sig in _DOSSIER_HINT_SIGNALS):
            dossier_hint_idx = m.index
    if dossier_hint_idx == -1:
        return False
    # Any prospect message after that index counts as a response
    return any(m.index > dossier_hint_idx for m in prospect_msgs)


# ── Engagement scoring ────────────────────────────────────────────────────────

def _score_engagement(
    prospect_msgs: List[Message],
    dossier_sent: bool,
    responded_to_dossier: bool,
) -> Engagement:
    if not prospect_msgs:
        return Engagement.LOW

    all_text   = ' '.join(m.text for m in prospect_msgs)
    word_count = len(all_text.split())
    emoji_count = len(_EMOJI_RE.findall(all_text))
    question_count = all_text.count('?')
    msg_count = len(prospect_msgs)

    score = 0

    # Volume signals
    if word_count > 60:
        score += 3
    elif word_count > 25:
        score += 2
    elif word_count > 8:
        score += 1

    # Emoji signals — any emoji in prospect response is a positive signal
    if emoji_count >= 3:
        score += 3
    elif emoji_count >= 1:
        score += 1

    # Interaction signals
    if question_count >= 1:
        score += 2
    if msg_count >= 3:
        score += 1

    # Dossier response is a strong positive signal
    if responded_to_dossier:
        score += 2

    if score >= 6:
        return Engagement.HIGH
    if score >= 3:
        return Engagement.MEDIUM
    return Engagement.LOW


# ── Temperature scoring ───────────────────────────────────────────────────────

def _score_temperature(engagement: Engagement, stage: Stage) -> Temperature:
    if stage == Stage.MEETING:
        return Temperature.HOT
    if engagement == Engagement.HIGH:
        return Temperature.HOT
    if engagement == Engagement.MEDIUM:
        return Temperature.WARM
    return Temperature.COLD


# ── Exact words extraction ────────────────────────────────────────────────────

def _extract_exact_words(prospect_msgs: List[Message]) -> List[str]:
    """
    Extract verbatim phrases from prospect messages.
    Returns individual sentences / short phrases — the Evidence Engine
    (HITO 3) will decide which ones are usable.
    """
    phrases = []
    for m in prospect_msgs:
        # Split by sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', m.text.strip())
        for s in sentences:
            s = s.strip()
            if s and len(s) > 3:
                phrases.append(s)
        # Also include the full message if short (≤ 10 words) and complete
        words = m.text.split()
        if 3 < len(words) <= 10:
            phrases.append(m.text.strip())
    # Deduplicate preserving order
    seen, unique = set(), []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


# ── Open question detection ───────────────────────────────────────────────────

def _find_open_question(
    hint_msgs: List[Message],
    prospect_msgs: List[Message],
) -> Optional[str]:
    """
    Return the last question asked by Hint that the prospect has not answered.
    Returns None if all questions were answered or no question exists.
    """
    if not hint_msgs:
        return None

    last_hint = hint_msgs[-1]
    # Extract questions from the last Hint message
    questions = re.findall(r'[^.!?]*\?', last_hint.text)
    if not questions:
        return None

    # If prospect has replied after this hint message, assume question was answered
    answered = any(m.index > last_hint.index for m in prospect_msgs)
    if answered:
        return None

    return questions[-1].strip() if questions else None
