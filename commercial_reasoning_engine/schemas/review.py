from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReviewViolation:
    rule: str                    # e.g. "blocklist" | "perspective" | "evidence_leak" | "cta"
    description: str
    detected_fragment: str       # exact fragment from draft that triggered the violation


@dataclass
class ReviewResult:
    approved: bool
    score: float                 # 0.0 - 1.0, 1.0 = all checks passed
    violations: List[ReviewViolation] = field(default_factory=list)
    final_message: Optional[str] = None  # None if not approved
