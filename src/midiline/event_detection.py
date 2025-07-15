from __future__ import annotations

from typing import List

import numpy as np

from .preprocess import frame_audio
from .events import NoteEvent


def _frame_rms(frames: np.ndarray) -> np.ndarray:
    """Root mean square energy for each frame."""
    frames = np.asarray(frames, dtype=float)
    if frames.ndim == 1:
        frames = frames[None, :]
    return np.sqrt(np.mean(frames ** 2, axis=1))


def _frame_pitch(frames: np.ndarray, sample_rate: int) -> np.ndarray:
    """Estimate pitch using zero-crossing rate."""
    frames = np.asarray(frames)
    if frames.ndim == 1:
        frames = frames[None, :]
    crossings = np.abs(np.diff(np.signbit(frames), axis=1))
    counts = np.sum(crossings, axis=1)
    freqs = np.where(
        counts >= 2, sample_rate * counts / (2 * frames.shape[1]), 0.0
    )
    return freqs


def detect_note_events(
    signal: np.ndarray,
    sample_rate: int,
    frame_size: int = 1024,
    hop_size: int = 512,
    energy_threshold: float = 0.2,
    pitch_tolerance: float = 30.0,
) -> List[NoteEvent]:
    """Detect musical events based on changes in energy and pitch.

    Parameters
    ----------
    signal:
        Monophonic audio signal.
    sample_rate:
        Sampling rate of ``signal``.
    frame_size:
        Number of samples per analysis frame.
    hop_size:
        Number of samples between consecutive frames.
    energy_threshold:
        Relative energy (0-1) used to detect an active note.
    pitch_tolerance:
        Minimum pitch change in Hz that will trigger a new note when energy is
        above threshold.
    """

    if len(signal) < frame_size:
        return []

    signal = np.asarray(signal, dtype=float)
    frames = frame_audio(signal, frame_size, hop_size)
    if len(frames) == 0:
        return []

    energies = _frame_rms(frames)
    pitches = _frame_pitch(frames, sample_rate)
    num_frames = len(frames)

    max_energy = float(np.max(energies))
    onset = 0 if energies[0] > energy_threshold * max_energy else None
    last_pitch = pitches[0]
    events: List[NoteEvent] = []

    for i in range(1, num_frames):
        energy = energies[i]
        pitch = pitches[i]

        if onset is None:
            if energy > energy_threshold * max_energy and (
                energies[i - 1] <= energy_threshold * max_energy
                or abs(pitch - last_pitch) > pitch_tolerance
            ):
                onset = i
        else:
            if energy <= energy_threshold * max_energy or abs(pitch - last_pitch) > pitch_tolerance:
                start_time = onset * hop_size / sample_rate
                end_time = i * hop_size / sample_rate
                amplitude = float(np.max(energies[onset:i]) / max_energy)
                events.append(NoteEvent(start_time, end_time, amplitude))
                onset = None
        last_pitch = pitch

    if onset is not None:
        start_time = onset * hop_size / sample_rate
        end_time = num_frames * hop_size / sample_rate
        amplitude = float(np.max(energies[onset:]) / max_energy)
        events.append(NoteEvent(start_time, end_time, amplitude))

    return events
