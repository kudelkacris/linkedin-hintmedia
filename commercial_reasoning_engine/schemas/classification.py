from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    MSG2 = "MSG2"
    SEG1 = "SEG1"
    SEG2 = "SEG2"
    WAIT = "WAIT"
    NONE = "NONE"


class StrategyType(str, Enum):
    CONSULTIVA   = "CONSULTIVA"    # Manager / Coordinator / Specialist
    ENTRE_PARES  = "ENTRE_PARES"  # Director / VP / C-Level / Founder
    EXPLORATORIA = "EXPLORATORIA" # insufficient info — no meeting proposal
    RECUPERACION = "RECUPERACION" # prospect went cold after high engagement


@dataclass
class ActionClassification:
    action: Action
    reason: str


@dataclass
class StrategyClassification:
    strategy: StrategyType
    reason: str
