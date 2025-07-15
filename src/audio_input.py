import time
from typing import Generator, Optional

import pyaudio


class AudioInput:
    """Simple wrapper around PyAudio for reading fixed-length audio blocks."""

    def __init__(self, device_index: Optional[int] = None, sample_rate: int = 44100,
                 buffer_size: int = 1024, channels: int = 1):
        """Initialize the audio input configuration.

        Parameters
        ----------
        device_index:
            Index of the audio device to use. If ``None`` the default device is
            selected.
        sample_rate:
            Sampling rate for the audio stream.
        buffer_size:
            Number of frames per block returned by :meth:`read`.
        channels:
            Number of audio channels to capture.
        """
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channels = channels
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None

    def open(self) -> None:
        """Open the input stream with the configured parameters."""
        if self._stream is not None:
            return
        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.buffer_size,
            input_device_index=self.device_index,
        )

    def read(self) -> bytes:
        """Read one block of audio from the stream."""
        if self._stream is None:
            raise RuntimeError("Stream is not open")
        return self._stream.read(self.buffer_size, exception_on_overflow=False)

    def blocks(self) -> Generator[bytes, None, None]:
        """Generator that yields audio blocks indefinitely."""
        try:
            while True:
                yield self.read()
        finally:
            self.close()

    def close(self) -> None:
        """Stop and close the stream and release PyAudio resources."""
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pyaudio is not None:
            self._pyaudio.terminate()
            self._pyaudio = None


def demo(duration: float = 5.0, **kwargs) -> None:
    """Simple demo that prints a few audio blocks for ``duration`` seconds."""
    ai = AudioInput(**kwargs)
    ai.open()
    start = time.time()
    for block in ai.blocks():
        print(block)
        if time.time() - start > duration:
            break
    ai.close()


if __name__ == "__main__":
    demo()
