import numpy as np
import mido

from .preprocess import highpass_filter
from .pitch_detection import FastYin


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
        pitch_threshold: float = 0.1,
        amp_threshold: float = 0.01,
        release_frames: int = 3,
        cutoff: float | None = None,
        velocity: int = 64,
        channel: int = 0,
        gate_threshold: float = 0.0,
        gate_attack: int = 2,
        gate_release: int = 10,
        onset_frames: int = 2,
    ) -> None:
        self.detector = FastYin(buffer_size * 2, samplerate, threshold=pitch_threshold)
        self.smoothing = 0.4
        self.smoothed_pitch = 0.0
        self.min_freq = 60.0
        self.max_freq = 10000.0
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
            samples = highpass_filter(samples, self.cutoff, self.samplerate)
        if self.gate:
            samples = self.gate.process(samples)

        amplitude = float(np.sqrt(np.dot(samples, samples) / len(samples)))
        pitch = float(self.detector(samples))
        if pitch > 0.0:
            self.smoothed_pitch = (
                self.smoothing * pitch + (1.0 - self.smoothing) * self.smoothed_pitch
            )
        else:
            self.smoothed_pitch *= 1.0 - self.smoothing

        in_range = self.min_freq <= self.smoothed_pitch <= self.max_freq
        active = amplitude > self.amp_threshold and in_range

        if active:
            self.onset_count += 1
        else:
            self.onset_count = 0

        if self.onset_count >= self.onset_frames and active:
            midi_note = int(round(69 + 12 * np.log2(self.smoothed_pitch / 440.0)))
            velocity = int(
                np.clip(amplitude / self.amp_threshold * self.velocity, 1, 127)
            )
            self.onset_count = 0
            self.release_count = 0
            if self.last_note is None or midi_note != self.last_note:
                if self.last_note is not None:
                    self.out_port.send(
                        mido.Message(
                            "note_off",
                            note=self.last_note,
                            velocity=0,
                            channel=self.channel,
                        )
                    )
                self.out_port.send(
                    mido.Message(
                        "note_on",
                        note=midi_note,
                        velocity=velocity,
                        channel=self.channel,
                    )
                )
                self.last_note = midi_note
        else:
            if amplitude <= self.amp_threshold:
                self.release_count += 1
            else:
                self.release_count = 0
            if self.last_note is not None and self.release_count >= self.release_frames:
                self.out_port.send(
                    mido.Message(
                        "note_off",
                        note=self.last_note,
                        velocity=0,
                        channel=self.channel,
                    )
                )
                self.last_note = None

    def close(self) -> None:
        if self.last_note is not None:
            self.out_port.send(
                mido.Message("note_off", note=self.last_note, velocity=0, channel=self.channel)
            )
        self.out_port.close()
