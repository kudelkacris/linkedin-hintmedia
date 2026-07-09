"""
strategy/win_selector.py — Select the personal win for a prospect.

Single responsibility: given seniority and engagement, return the most
relevant win from config/win_personal.json.

Rule:
  engagement == LOW  → None (insufficient signal to assume relevance)
  engagement >= MEDIUM → first win for seniority (most applicable per config order)
"""
import json
from pathlib import Path
from typing import Optional

from ..schemas.analysis import Seniority, Engagement

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "win_personal.json"
_WIN_PERSONAL: dict = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def select_win(seniority: Seniority, engagement: Engagement) -> Optional[str]:
    """
    Return the first personal win for this seniority level.
    Returns None when engagement is LOW — not enough signal.
    """
    if engagement == Engagement.LOW:
        return None

    wins = _WIN_PERSONAL.get(seniority.value) or _WIN_PERSONAL.get("OTHER", [])
    return wins[0] if wins else None
