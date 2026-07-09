"""
reviewer/evidence_checker.py — Forbidden claim leak detection.

Rule: forbidden_claims must NEVER appear in the draft as stated facts.
These are INFERRED claims — never confirmed by the prospect.

"Aunque sea cierto. Aunque Claude lo sepa. Aunque LinkedIn lo diga.
No importa. No estaba permitido." — HITO 8 brief.

Detection strategy:
  1. Trigram overlap: extract 3-word sequences from each forbidden claim
     and check if they appear in the draft.
  2. Bigram fallback for short claims (< 3 words).

Conservative by design: a false positive (rejecting a safe draft) is
preferable to a false negative (letting an inferred claim through).
"""
import re
from typing import List, Set

from ..schemas.context import LLMContext
from ..schemas.review import ReviewViolation


def check(draft: str, context: LLMContext) -> List[ReviewViolation]:
    """
    Scan the draft for n-gram overlap with forbidden_claims.
    Returns one violation per leaked claim.
    """
    if not context.forbidden_claims:
        return []

    draft_trigrams = _extract_ngrams(draft, n=3)
    draft_bigrams = _extract_ngrams(draft, n=2)
    violations: List[ReviewViolation] = []

    for claim in context.forbidden_claims:
        words = _tokenize(claim)
        if len(words) >= 3:
            claim_grams = _extract_ngrams(claim, n=3)
            overlap = draft_trigrams & claim_grams
        elif len(words) == 2:
            claim_grams = _extract_ngrams(claim, n=2)
            overlap = draft_bigrams & claim_grams
        else:
            # Single word claim — check exact word presence
            overlap = {words[0]} if words and words[0] in _tokenize(draft) else set()

        if overlap:
            matched = sorted(overlap)[0]  # deterministic: first alphabetically
            violations.append(ReviewViolation(
                rule="evidence_leak",
                description=(
                    f"Inferencia filtrada al draft: '{claim}'"
                ),
                detected_fragment=f"secuencia encontrada: '{matched}'",
            ))

    return violations


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    return re.findall(r'\b\w+\b', text.lower())


def _extract_ngrams(text: str, n: int) -> Set[str]:
    words = _tokenize(text)
    if len(words) < n:
        return set()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}
