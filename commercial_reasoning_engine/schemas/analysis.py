from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Stage(str, Enum):
    MSG1_SENT      = "1"
    MSG2_SENT      = "2"
    DOSSIER_SENT   = "3"
    SEG1_SENT      = "4"
    MEETING        = "6"
    UNKNOWN        = "0"


class Engagement(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"


class Seniority(str, Enum):
    CEO       = "CEO"
    DIRECTOR  = "DIRECTOR"
    MANAGER   = "MANAGER"
    SPECIALIST = "SPECIALIST"
    OTHER     = "OTHER"


class Temperature(str, Enum):
    COLD = "FRIA"
    WARM = "TIBIA"
    HOT  = "CALIENTE"


@dataclass
class AnalysisResult:
    stage: Stage
    engagement: Engagement
    sector: str
    seniority: Seniority
    is_decision_maker: bool
    last_prospect_message: str
    dossier_sent: bool
    days_since_dossier: Optional[int]
    responded_to_dossier: bool
    open_question: Optional[str]          # question left unanswered by prospect
    prospect_exact_words: List[str]       # verbatim phrases from prospect
    previous_msg2_angle: Optional[str]    # angle used in MSG2, for rotation
    temperature: Temperature
