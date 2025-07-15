import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pytest

from src.preprocess import normalize, frame_audio


def test_normalize_range():
    audio = np.array([0.5, -1.0, 0.25])
    norm_audio = normalize(audio)
    assert np.isclose(np.max(np.abs(norm_audio)), 1.0)


def test_frame_audio_shape():
    audio = np.arange(10)
    frames = frame_audio(audio, frame_size=4, hop_size=2)
    assert frames.shape == (4, 4)
    assert np.all(frames[0] == np.array([0, 1, 2, 3]))

from src.preprocess import lowpass_filter as lp_root
from src.midiline.preprocess import lowpass_filter as lp_pkg


def test_lowpass_filter_preserves_dtype_root():
    audio = np.random.rand(1024).astype(np.float32)
    filt = lp_root(audio, cutoff=1000, fs=44100)
    assert filt.dtype == np.float32


def test_lowpass_filter_preserves_dtype_pkg():
    audio = np.random.rand(1024).astype(np.float32)
    filt = lp_pkg(audio, cutoff=1000, fs=44100)
    assert filt.dtype == np.float32
