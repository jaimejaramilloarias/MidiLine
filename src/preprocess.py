import numpy as np
from scipy.signal import butter, lfilter


def normalize(audio):
    """Normalize ``audio`` to the range ``[-1, 1]``.

    An empty array is returned unchanged. ``audio`` is converted to ``float``
    before processing.
    """
    audio = np.asarray(audio, dtype=float)
    if audio.size == 0:
        return audio
    max_val = float(np.max(np.abs(audio)))
    if max_val == 0:
        return audio
    return audio / max_val


def lowpass_filter(audio, cutoff, fs=44100, order=5):
    """Apply a Butterworth low-pass filter preserving float32 precision."""
    audio = np.asarray(audio, dtype=np.float32)
    nyq = 0.5 * fs
    norm_cutoff = cutoff / nyq
    b, a = butter(order, norm_cutoff, btype='low', analog=False)
    filtered = lfilter(b, a, audio)
    return filtered.astype(np.float32, copy=False)


def frame_audio(audio, frame_size, hop_size):
    """Split audio into overlapped frames."""
    audio = np.asarray(audio)
    if len(audio) < frame_size:
        return np.empty((0, frame_size))
    num_frames = 1 + (len(audio) - frame_size) // hop_size
    shape = (num_frames, frame_size)
    frames = np.lib.stride_tricks.as_strided(
        audio,
        shape=shape,
        strides=(hop_size * audio.strides[0], audio.strides[0])
    )
    return frames.copy()
