"""
reviewer/reviewer.py — Orchestrates all draft checks.

The reviewer is the gatekeeper between the LLM draft and the user.
A draft that fails any single check is rejected entirely.
The caller (run.py) decides whether to retry or surface the error.

Authority inversion: from this point on, the LLM must earn approval.
"""
from ..schemas.context import LLMContext
from ..schemas.review import ReviewResult, ReviewViolation
from . import blocklist_checker, perspective_checker, evidence_checker


_CHECKER_RULES = ["blocklist", "perspective", "evidence_leak"]
_N_CHECKERS = len(_CHECKER_RULES)


def review(draft: str, context: LLMContext) -> ReviewResult:
    """
    Run all checkers against the draft. Return ReviewResult.
    approved=True only if ALL checkers pass (zero violations).
    score is the fraction of checkers that passed (1.0 = clean).
    """
    violations: list[ReviewViolation] = []

    violations.extend(blocklist_checker.check(draft, context))
    violations.extend(perspective_checker.check(draft, context))
    violations.extend(evidence_checker.check(draft, context))

    failed_rules = {v.rule for v in violations}
    passed = _N_CHECKERS - len(failed_rules)
    score = round(passed / _N_CHECKERS, 4)
    approved = len(violations) == 0

    return ReviewResult(
        approved=approved,
        score=score,
        violations=violations,
        final_message=draft if approved else None,
    )
