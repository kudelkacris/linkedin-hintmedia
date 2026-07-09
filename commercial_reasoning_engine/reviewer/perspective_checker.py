"""
reviewer/perspective_checker.py — Perspective rule enforcement.

Rule (CLAUDE.md): "Si el primer sujeto de una oración es 'nosotros',
'trabajo con', 'en Hint', 'nuestra empresa' → detener y reescribir."

The protagonist of the first bubble must be the PROSPECT, not Hint Media.
Hint may appear later (B3). It must NOT be the opener.
"""
import re
from typing import List

from ..schemas.context import LLMContext
from ..schemas.review import ReviewViolation


# Patterns that, if they are the START of the first content line, indicate
# that Hint / the sender is the protagonist instead of the prospect.
# These are checked after stripping the greeting line.
_FORBIDDEN_OPENERS = [
    r"^en hint\b",
    r"^trabajo con\b",
    r"^somos\b",
    r"^nosotros\b",
    r"^nuestra empresa\b",
    r"^nuestra agencia\b",
    r"^desde hint\b",
    r"^hint media es\b",
    r"^hint media hace\b",
    r"^hint media trabaja\b",
    r"^hint media te\b",
    r"^hint media, una\b",
]

_GREETING_PREFIX = re.compile(r"^buenas\b", re.IGNORECASE)


def check(draft: str, context: LLMContext) -> List[ReviewViolation]:
    """
    Verify the first content line (after greeting) starts from the prospect's world.
    Returns violations if the first subject is Hint / sender.
    """
    lines = [l.strip() for l in draft.splitlines() if l.strip()]
    if not lines:
        return []

    # Skip greeting line ("Buenas Nombre!")
    content_lines = lines[1:] if _GREETING_PREFIX.match(lines[0]) else lines

    if not content_lines:
        return []

    first_line = content_lines[0].lower()

    for pattern in _FORBIDDEN_OPENERS:
        if re.match(pattern, first_line, re.IGNORECASE):
            return [ReviewViolation(
                rule="perspective",
                description=(
                    "La primera línea empieza desde Hint/nosotros en vez del prospecto. "
                    f"Patrón detectado: '{pattern}'"
                ),
                detected_fragment=content_lines[0][:80],
            )]

    return []
