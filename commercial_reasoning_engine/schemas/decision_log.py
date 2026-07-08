from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class DecisionLogStep:
    module: str
    output_summary: Dict[str, Any]   # key facts from this module's output
    duration_ms: int
    timestamp: str                   # ISO format


@dataclass
class DecisionTrace:
    run_id: str                      # "{YYYY-MM-DD}_{HH-MM-SS}_{prospect_slug}"
    prospect: str
    steps: List[DecisionLogStep] = field(default_factory=list)
    final_message: Optional[str] = None
    approved: bool = False
    blocked: bool = False
    block_reason: Optional[str] = None
    total_duration_ms: int = 0
