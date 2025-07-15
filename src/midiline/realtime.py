import numpy as np
import mido
import aubio
from collections import deque

from .preprocess import lowpass_filter


class NoiseGate:
    """Simple noise gate with attack and release fade."""

    def __init__(self, threshold: float, attack: int, release: int) -> None:
        self.threshold = float(threshold)
        self.attack = max(1, int(attack))
        self.release = max(1, int(release))
        self.gain = 0.0

    def process(self, frame: np.ndarray) -> np.ndarray:
        rms = float(np.sqrt(np.dot(frame, frame) / len(frame)))
        if rms >= self.threshold:
            self.gain = min(1.0, self.gain + 1.0 / self.attack)
        else:
            self.gain = max(0.0, self.gain - 1.0 / self.release)
        return frame * self.gain


class RealTimeProcessor:
    """Convert incoming audio blocks to MIDI messages with smoothing."""

    def __init__(
        self,
        midi_port: str = "MidiLine",
        buffer_size: int = 1024,
        samplerate: int = 44100,
        tolerance: float = 0.8,
        amp_threshold: float = 0.01,
        history_size: int = 5,
        release_frames: int = 5,
        cutoff: float | None = None,
        velocity: int = 64,
        channel: int = 0,
        gate_threshold: float = 0.0,
        gate_attack: int = 2,
        gate_release: int = 10,
        onset_frames: int = 2,
        silence: float = -40.0,
    ) -> None:
        self.pitch_o = aubio.pitch("yin", buffer_size * 2, buffer_size, samplerate)
        self.pitch_o.set_unit("midi")
        self.pitch_o.set_silence(silence)
        self.pitch_o.set_tolerance(tolerance)
        self.pitch_tolerance = float(tolerance)

        self.history = deque(maxlen=history_size)
        self.amp_threshold = amp_threshold
        self.release_frames = release_frames
        self.cutoff = cutoff
        self.samplerate = samplerate
        self.velocity = int(velocity)
        self.channel = int(channel)
        self.gate = (
            NoiseGate(gate_threshold, gate_attack, gate_release)
            if gate_threshold > 0.0
            else None
        )
        self.onset_frames = max(1, int(onset_frames))
        self.onset_count = 0

        try:
            self.out_port = mido.open_output(midi_port, virtual=True)
        except IOError:
            self.out_port = mido.open_output(midi_port)

        self.last_note: int | None = None
        self.release_count = 0

    def process_block(self, samples: np.ndarray) -> None:
        """Process one block of audio samples."""
        if self.cutoff:
            samples = lowpass_filter(samples, self.cutoff, self.samplerate)
        if self.gate:
            samples = self.gate.process(samples)
        # Efficient RMS computation without allocating intermediate arrays
        amplitude = float(np.sqrt(np.dot(samples, samples) / len(samples)))
        pitch = self.pitch_o(samples)[0]
        confidence = self.pitch_o.get_confidence()

        self.history.append(pitch)
        smoothed_pitch = float(np.median(self.history))
        should_trigger = (
            amplitude > self.amp_threshold
            and pitch > 0
            and confidence >= self.pitch_tolerance
        )

        if should_trigger:
            self.onset_count += 1
        else:
            self.onset_count = 0

        if self.onset_count >= self.onset_frames and should_trigger:
            note = int(round(smoothed_pitch))
            bend = int(np.clip((smoothed_pitch - note) * 8192, -8192, 8191))
            velocity = int(
                np.clip(amplitude / self.amp_threshold * self.velocity, 1, 127)
            )
            self.onset_count = 0
            self.release_count = 0
            if self.last_note is None or note != self.last_note:
                if self.last_note is not None:
                    self.out_port.send(
                        mido.Message(
                            "note_off",
                            note=self.last_note,
                            velocity=0,
                            channel=self.channel,
                        )
                    )
                self.out_port.send(mido.Message("pitchwheel", pitch=bend, channel=self.channel))
                self.out_port.send(
                    mido.Message(
                        "note_on",
                        note=note,
                        velocity=velocity,
                        channel=self.channel,
                    )
                )
                self.last_note = note
            else:
                self.out_port.send(mido.Message("pitchwheel", pitch=bend, channel=self.channel))
        else:
            if self.last_note is not None and should_trigger:
                bend = int(np.clip((smoothed_pitch - self.last_note) * 8192, -8192, 8191))
                self.out_port.send(mido.Message("pitchwheel", pitch=bend, channel=self.channel))
            if amplitude <= self.amp_threshold:
                self.release_count += 1
            else:
                # Don't cut the note if the signal is loud but pitch detection
                # momentarily fails. Reset the release counter in that case so
                # the note sustains smoothly.
                self.release_count = 0
            if self.last_note is not None and self.release_count >= self.release_frames:
                self.out_port.send(
                    mido.Message(
                        "note_off", note=self.last_note, velocity=0, channel=self.channel
                    )
                )
                self.last_note = None

    def close(self) -> None:
        if self.last_note is not None:
            self.out_port.send(
                mido.Message("note_off", note=self.last_note, velocity=0, channel=self.channel)
            )
        self.out_port.close()
