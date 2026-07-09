"""
reviewer/blocklist_checker.py — Hard phrase blocklist enforcement.

Checks the draft for any phrase from the master blocklist.
Zero tolerance: one match = FAIL. No partial credit.

Source: CLAUDE.md BLOCKLIST section.
"""
import re
from typing import List

from ..schemas.context import LLMContext
from ..schemas.review import ReviewViolation


# Phrases extracted verbatim from CLAUDE.md blocklist.
# Each entry is a tuple: (pattern_string, human_label)
# pattern_string: case-insensitive substring to search.
_BLOCKLIST: List[tuple[str, str]] = [
    # Apertura
    ("por la apertura", "variante de 'gracias por la apertura'"),
    ("con apertura", "variante de 'gracias por la apertura'"),
    ("me abre la posibilidad", "variante de 'gracias por la apertura'"),
    # Razón de contacto
    ("por eso pensé en escribirte", "frase de razón de contacto"),
    ("por eso te escribo", "frase de razón de contacto"),
    ("te escribo porque", "frase de razón de contacto"),
    # Pitch clichés
    ("es un desafío que vemos seguido", "cliché de pitch"),
    ("justamente por eso", "cliché de pitch"),
    ("exactamente donde trabajamos", "cliché de pitch"),
    ("muchas empresas", "generalización prohibida"),
    ("somos una agencia", "auto-descripción prohibida"),
    # Seguimiento
    ("no sé si viste", "frase de seguimiento"),
    ("no se si viste", "frase de seguimiento"),
    ("retomo", "frase de seguimiento"),
    ("vuelvo a escribirte", "frase de seguimiento"),
    ("no quería dejar de escribirte", "frase de seguimiento"),
    ("quería hacer seguimiento", "frase de seguimiento"),
    ("queria hacer seguimiento", "frase de seguimiento"),
    ("más allá del dossier", "frase de seguimiento"),
    ("mas alla del dossier", "frase de seguimiento"),
    # Cierre
    ("quedo atento", "cierre prohibido"),
    ("quedo atenta", "cierre prohibido"),
    ("cualquier duda", "cierre prohibido"),
    # Atribución de cargo
    ("vi que sos", "abrir con cargo prohibido"),
    ("veo que sos", "abrir con cargo prohibido"),
    ("como responsable de", "abrir con cargo prohibido"),
    ("como gerente de", "abrir con cargo prohibido"),
    # Atribución falsa
    ("me comentabas", "atribuir palabras al prospecto sin cita real"),
    ("como me contabas", "atribuir palabras al prospecto sin cita real"),
    ("me decías que", "atribuir palabras al prospecto sin cita real"),
    ("me decias que", "atribuir palabras al prospecto sin cita real"),
]


def check(draft: str, context: LLMContext) -> List[ReviewViolation]:
    """Return one ReviewViolation per blocklist phrase found in draft."""
    draft_lower = draft.lower()
    violations: List[ReviewViolation] = []

    for phrase, label in _BLOCKLIST:
        if phrase in draft_lower:
            # Find the actual fragment in the draft for reporting
            idx = draft_lower.find(phrase)
            # Extract up to 60 chars of surrounding context
            start = max(0, idx - 10)
            end = min(len(draft), idx + len(phrase) + 20)
            fragment = draft[start:end].strip()

            violations.append(ReviewViolation(
                rule="blocklist",
                description=f"Frase prohibida ({label}): '{phrase}'",
                detected_fragment=fragment,
            ))

    return violations
