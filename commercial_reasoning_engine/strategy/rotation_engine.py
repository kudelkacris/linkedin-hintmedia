"""
strategy/rotation_engine.py — Rotate MSG2 angle to mandatory SEG1 angle.

Single responsibility: map a previous MSG2 angle to the angle SEG1 must use.
Reads config/rotation_map.json. Never decides if rotation is needed — only computes it.
"""
import json
from pathlib import Path
from typing import Tuple, Optional

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "rotation_map.json"
_ROTATION_MAP: dict = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
_KNOWN_KEYS = [k for k in _ROTATION_MAP if k != "default"]


def rotate(previous_angle: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Map previous_angle → (rotation_applied, new_angle).

    Returns:
        (False, None)                          if previous_angle is None/empty
        (True,  rotation_map[key]["rotate_to"]) on exact match
        (True,  rotation_map[key]["rotate_to"]) on substring match
        (True,  rotation_map["default"]["rotate_to"]) if no key matches
    """
    if not previous_angle:
        return False, None

    # Exact match
    if previous_angle in _ROTATION_MAP:
        return True, _ROTATION_MAP[previous_angle]["rotate_to"]

    # Substring match — key is fragment of angle or angle is fragment of key
    lower = previous_angle.lower().strip()
    for key in _KNOWN_KEYS:
        if key in lower or lower in key:
            return True, _ROTATION_MAP[key]["rotate_to"]

    # Default fallback
    return True, _ROTATION_MAP["default"]["rotate_to"]
