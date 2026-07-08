from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    speaker: str        # "prospect" | "hint" | "unknown"
    text: str
    index: int          # position in conversation, 0-based


@dataclass
class ConversationInput:
    raw_text: str
    prospect_name: str
    messages: List[Message] = field(default_factory=list)
    prospect_file_path: Optional[str] = None   # path to conversaciones/*.md if found
