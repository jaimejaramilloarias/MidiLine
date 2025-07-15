from dataclasses import dataclass
from typing import Optional

@dataclass
class NoteEvent:
    """Representation of a musical note event."""

    start: float
    end: float
    amplitude: float = 0.0
    note: Optional[int] = None
    velocity: Optional[int] = None
    channel: int = 0
