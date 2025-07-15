import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
from src.pitch_detection import yin, pitch_track


def generate_sine(freq: float, sr: int, duration: float) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def test_yin_detects_440hz():
    sr = 22050
    tone = generate_sine(440.0, sr, 1.0)
    f0 = yin(tone[:2048], sr)
    assert abs(f0 - 440.0) < 1.5


def test_pitch_track_smoothing():
    sr = 22050
    tone = generate_sine(220.0, sr, 1.0)
    pitches = pitch_track(tone, sr, frame_size=1024, hop_size=512, smooth=7)
    median_pitch = np.median(pitches)
    assert abs(median_pitch - 220.0) < 1.0
