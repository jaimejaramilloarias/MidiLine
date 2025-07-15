from typing import Iterable
import time
import mido

from .events import NoteEvent

class MidiOutput:
    """Send NoteOn/NoteOff messages to a MIDI output port."""

    def __init__(self, port_name: str = "MidiLine Output"):
        # Create a virtual output so DAWs can connect.
        self.port = mido.open_output(port_name, virtual=True)

    def play(self, events: Iterable[NoteEvent]):
        """Play a sequence of NoteEvents in real time."""
        start_time = time.time()
        for event in sorted(events, key=lambda e: e.start):
            now = time.time()
            wait = event.start - (now - start_time)
            if wait > 0:
                time.sleep(wait)
            note_on = mido.Message(
                'note_on', note=event.note, velocity=event.velocity, channel=event.channel
            )
            self.port.send(note_on)
            duration = max(event.end - event.start, 0)
            if duration > 0:
                time.sleep(duration)
            note_off = mido.Message(
                'note_off', note=event.note, velocity=0, channel=event.channel
            )
            self.port.send(note_off)

    def close(self):
        if self.port:
            self.port.close()
