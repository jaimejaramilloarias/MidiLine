import numpy as np
from scipy.signal import medfilt


def yin(frame: np.ndarray, sr: int, threshold: float = 0.1) -> float:
    """Estimate fundamental frequency of an audio frame using the YIN algorithm.

    Parameters
    ----------
    frame : np.ndarray
        Audio samples of the frame (mono).
    sr : int
        Sampling rate of the audio.
    threshold : float
        Threshold for the normalized difference function.

    Returns
    -------
    float
        Estimated fundamental frequency in Hz. Returns 0.0 if no pitch is
        found.
    """
    frame = frame.astype(float)
    n = len(frame)
    if n == 0:
        return 0.0

    max_tau = n // 2
    diffs = np.zeros(max_tau)
    for tau in range(1, max_tau):
        delta = frame[:max_tau] - frame[tau:tau + max_tau]
        diffs[tau] = np.sum(delta * delta)

    cmnd = np.zeros_like(diffs)
    cmnd[0] = 1
    running_sum = 0.0
    for tau in range(1, max_tau):
        running_sum += diffs[tau]
        cmnd[tau] = diffs[tau] * tau / running_sum if running_sum != 0 else 1

    tau = 0
    for i in range(1, max_tau - 1):
        if cmnd[i] < threshold and cmnd[i] <= cmnd[i + 1]:
            tau = i
            break
    if tau == 0:
        tau = np.argmin(cmnd[1:]) + 1

    if tau == 0:
        return 0.0

    better_tau = float(tau)
    if 1 <= tau < max_tau - 1:
        x0, x1, x2 = cmnd[tau - 1], cmnd[tau], cmnd[tau + 1]
        denom = 2 * (2 * x1 - x2 - x0)
        if denom != 0:
            better_tau = tau + (x2 - x0) / denom

    return float(sr) / better_tau


def pitch_track(signal: np.ndarray, sr: int, frame_size: int = 2048,
                hop_size: int = 512, threshold: float = 0.1,
                smooth: int = 5) -> np.ndarray:
    """Track pitch over time using YIN and apply median smoothing."""
    pitches = []
    for start in range(0, len(signal) - frame_size + 1, hop_size):
        frame = signal[start:start + frame_size]
        pitches.append(yin(frame, sr, threshold))
    pitches = np.array(pitches)
    if smooth > 1:
        pitches = medfilt(pitches, kernel_size=smooth)
    return pitches
