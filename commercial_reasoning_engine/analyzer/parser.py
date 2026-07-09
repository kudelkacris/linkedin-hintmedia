"""
analyzer/parser.py — Convert raw LinkedIn conversation text into ConversationInput.

Single responsibility: structure raw text. No analysis. No decisions.
"""
import re
from typing import Optional, List

from ..schemas.conversation import ConversationInput, Message

# Signals that a block was written by Hint Media
_HINT_SIGNALS = re.compile(
    r'Buenas \w+!'
    r'|\bHint Media\b'
    r'|\bdossier\b'
    r'|te puedo enviar'
    r'|trabajamos con'
    r'|Libra Seguros|Destiny Group|TGS|Transener|Tasarolli'
    r'|por acá si no es mucha molestia'
    r'|indicarías a quién'
    r'|ten[íi]a una consulta'
    r'|quer[íi]a saber si me pod[íi]as'
    r'|quer[íi]a consultarte'
    r'|quer[íi]a preguntarte',
    re.IGNORECASE,
)

# Signals that a block was written by the prospect (override hint detection)
_PROSPECT_SIGNALS = re.compile(
    r'^(?:Hola|Buenas|Buenos\s+d[íi]as)\s+Florencia',
    re.IGNORECASE,
)

# A block containing only emojis/spaces is a prospect reaction
_EMOJI_ONLY = re.compile(
    r'^[\U0001F300-\U0001F9FF\U00010000-\U0010FFFF\s]+$',
    re.UNICODE,
)

# Patterns to extract the prospect's first name from the first Hint message
_NAME_FROM_GREETING = re.compile(
    r'(?:Buenas|Hola)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)[!,.]',
)
_NAME_FROM_OPENING = re.compile(
    r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)[,!.]',
)


def parse(raw_text: str, prospect_name: Optional[str] = None) -> ConversationInput:
    """
    Convert raw LinkedIn conversation text into a structured ConversationInput.

    Args:
        raw_text: The conversation as pasted — no special format required.
        prospect_name: Override if already known (e.g., from a .md filename).
    """
    blocks = _split_blocks(raw_text)

    if not prospect_name:
        prospect_name = _extract_name(blocks) or "Unknown"

    messages = _label_speakers(blocks, prospect_name)

    return ConversationInput(
        raw_text=raw_text,
        prospect_name=prospect_name,
        messages=messages,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _split_blocks(text: str) -> List[str]:
    """Split text into message blocks by blank lines."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    blocks = [b.strip() for b in re.split(r'\n{2,}', text)]
    return [b for b in blocks if b]


def _extract_name(blocks: List[str]) -> Optional[str]:
    """Try to extract prospect's first name from the first Hint message."""
    if not blocks:
        return None
    first = blocks[0]
    m = _NAME_FROM_GREETING.search(first)
    if m:
        return m.group(1)
    m = _NAME_FROM_OPENING.match(first)
    if m:
        return m.group(1)
    return None


def _is_hint_block(block: str) -> bool:
    """Heuristic: does this block look like a message from Hint Media?"""
    if _HINT_SIGNALS.search(block):
        return True
    # Long, structured messages (>40 words) are likely from Hint
    if len(block.split()) > 40:
        return True
    return False


def _label_speakers(blocks: List[str], prospect_name: str) -> List[Message]:
    """
    Assign 'hint' or 'prospect' to each block.

    Strategy:
    1. Explicit prospect signal (addresses Florencia) → 'prospect'
    2. Explicit hint signal match → 'hint'
    3. Emoji-only block → 'prospect'
    4. First block with no signals → 'hint' (MSG1 is always from Hint)
    5. Alternating fallback using previous speaker
    """
    messages: List[Message] = []

    for i, block in enumerate(blocks):
        if _PROSPECT_SIGNALS.match(block.strip()):
            speaker = "prospect"
        elif _is_hint_block(block):
            speaker = "hint"
        elif _EMOJI_ONLY.match(block):
            speaker = "prospect"
        elif i == 0:
            speaker = "hint"  # first message is always MSG1 from Hint
        else:
            # Fallback: alternate from the previous known speaker
            prev = messages[-1].speaker if messages else "hint"
            speaker = "prospect" if prev == "hint" else "hint"

        messages.append(Message(speaker=speaker, text=block, index=i))

    return messages
