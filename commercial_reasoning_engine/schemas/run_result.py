from dataclasses import dataclass
from typing import Optional

from .analysis import AnalysisResult
from .classification import ActionClassification, StrategyClassification
from .context import LLMContext
from .evidence import EvidenceInventory
from .review import ReviewResult
from .strategy import StrategyDecision


@dataclass
class RunResult:
    """
    Full output of a CRE pipeline run.
    Carries both the user-facing answer and the complete internal trace.
    """
    # ── User-facing ────────────────────────────────────────────────────────────
    approved: bool
    final_message: Optional[str]     # None if blocked, WAIT, or reviewer rejected
    blocked: bool                    # True if pipeline stopped early
    block_reason: Optional[str]      # reason for early stop
    action: str                      # "MSG2" | "SEG1" | "SEG2" | "WAIT" | "NONE"

    # ── Full trace (for debug, logging, future analysis) ──────────────────────
    prospect_name: str
    analysis: AnalysisResult
    evidence: EvidenceInventory
    action_cl: ActionClassification
    strategy_cl: StrategyClassification
    decision: StrategyDecision
    context: Optional[LLMContext]     # None if blocked before context_builder
    draft: Optional[str]              # None if blocked before llm adapter
    review: Optional[ReviewResult]    # None if blocked before reviewer
