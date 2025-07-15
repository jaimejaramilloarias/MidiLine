import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from event_detection import detect_note_events


def test_detect_note_events_simple():
    sr = 22050
    t = np.linspace(0, 1.0, sr, endpoint=False)
    first = np.sin(2 * np.pi * 440 * t[: sr // 2])
    second = 0.5 * np.sin(2 * np.pi * 660 * t[: sr // 2])
    signal = np.concatenate([first, second])

    events = detect_note_events(signal, sr, energy_threshold=0.1)

    assert len(events) == 2
    assert abs(events[0].start - 0.0) < 0.01
    assert abs(events[0].end - 0.5) < 0.05
    assert events[0].amplitude > events[1].amplitude
