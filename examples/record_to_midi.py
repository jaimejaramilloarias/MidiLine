"""Example script that sends a few notes via a virtual MIDI port."""
import os, sys; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
import time
from midi_output import MidiOutput
from events import NoteEvent


def main():
    midi = MidiOutput()
    events = [
        NoteEvent(note=60, velocity=100, start=0.0, end=0.5),
        NoteEvent(note=64, velocity=100, start=0.5, end=1.0),
        NoteEvent(note=67, velocity=100, start=1.0, end=1.5),
    ]
    try:
        midi.play(events)
    finally:
        midi.close()


if __name__ == "__main__":
    main()
