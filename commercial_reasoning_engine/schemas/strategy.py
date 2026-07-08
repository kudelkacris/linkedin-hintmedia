from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Bubble:
    id: str         # "B1" | "B2" | "B3" | "B4"
    objective: str  # single sentence describing what this bubble must accomplish


@dataclass
class CTADecision:
    allowed: bool
    type: Optional[str] = None           # "CONSULTIVA" | "ENTRE_PARES"
    suggested_phrase: Optional[str] = None


@dataclass
class StrategyDecision:
    unique_objective: str                 # the ONE commercial goal for this message
    opening_angle: Optional[str]          # None if no REAL evidence available
    opening_angle_source: str             # always "REAL" — INFERRED is never allowed here
    mention_hint: bool
    mention_dossier: bool
    propose_meeting: bool
    cta: CTADecision
    personal_win: Optional[str]           # what the PROSPECT gains as a person
    reference_client: Optional[str]       # Hint client chosen for this sector
    rotation_applied: bool
    previous_angle: Optional[str]         # angle used in MSG2
    new_angle: Optional[str]              # rotated angle for SEG1
    bubbles: List[Bubble] = field(default_factory=list)
    meeting_justification: Optional[str] = None  # mandatory if propose_meeting=True
    blocked: bool = False
    block_reason: Optional[str] = None
