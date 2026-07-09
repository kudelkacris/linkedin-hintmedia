from dataclasses import dataclass, field
from typing import List, Optional
from .strategy import Bubble, CTADecision


@dataclass
class FormatRules:
    greeting: str                       # "Buenas {name}!"
    no_long_dash: bool = True           # never use —
    no_opening_punctuation: bool = True # never use ¡ or ¿
    max_lines_per_bubble: int = 2
    bubble_separator: str = "\n"        # single newline between bubbles


@dataclass
class LLMContext:
    """
    The only thing the LLM receives.
    No full conversation. No .md file. No CLAUDE.md.
    Just this.
    """
    prospect_name: str
    engagement: str
    objective: str
    message_type: str                   # "MSG2" | "SEG1" | "SEG2"
    opening_angle: Optional[str]        # exact text or rotated angle to open with
    tone: str                           # derived from engagement + strategy + conv_mode

    allowed_topics: List[str]           # topics the LLM may reference
    forbidden_topics: List[str]         # topics the LLM must not mention
    allowed_claims: List[str]           # exact quotes from prospect the LLM may use
    forbidden_claims: List[str]         # inferred claims — must never appear

    cta: CTADecision
    personal_win: Optional[str]
    reference_client: Optional[str]
    conversation_mode: str              # "NORMAL" | "RECUPERACION"

    bubbles: List[Bubble]
    format_rules: FormatRules
