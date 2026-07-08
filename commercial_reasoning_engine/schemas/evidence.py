from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class EvidenceType(str, Enum):
    REAL     = "REAL"       # from the conversation itself, verbatim
    INFERRED = "INFERRED"   # derived from sector, profile, or assumption
    UNKNOWN  = "UNKNOWN"    # information we don't have


class EvidenceSource(str, Enum):
    CONVERSATION = "conversacion"
    PROFILE      = "perfil"
    SECTOR       = "sector"
    UNKNOWN      = "desconocido"


@dataclass
class Evidence:
    id: str                          # e.g. "EV001"
    claim: str                       # what is being asserted
    source: EvidenceSource
    type: EvidenceType
    usable: bool                     # False if INFERRED or UNKNOWN — enforced by validator
    exact_quote: Optional[str] = None  # only populated if type == REAL


@dataclass
class EvidenceInventory:
    all_evidence: List[Evidence] = field(default_factory=list)
    evidence_real_ids: List[str] = field(default_factory=list)
    evidence_inferred_ids: List[str] = field(default_factory=list)
    evidence_unknown_ids: List[str] = field(default_factory=list)
    opening_available: bool = False
    opening_evidence_id: Optional[str] = None  # id of the REAL evidence to open with
    blocked: bool = False
    block_reason: Optional[str] = None

    # Fundamental rule: if evidence_real_ids is empty → blocked = True.
    # This is enforced by evidence_engine/validator.py, not here.
