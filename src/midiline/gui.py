import sys
import threading
import sounddevice as sd
from .realtime import RealTimeProcessor
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QComboBox,
    QLineEdit,
)
from PyQt5.QtCore import Qt


class RecorderThread(threading.Thread):
    def __init__(
        self,
        device,
        buffer_size,
        midi_port,
        amp_threshold,
        pitch_threshold,
        samplerate=44100,
        input_channel=0,
    ):
        super().__init__(daemon=True)
        self.device = device
        self.buffer_size = buffer_size
        self.samplerate = samplerate
        self.midi_port = midi_port
        self.amp_threshold = amp_threshold
        self.pitch_threshold = pitch_threshold
        self.input_channel = int(input_channel)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        processor = RealTimeProcessor(
            midi_port=self.midi_port,
            buffer_size=self.buffer_size,
            samplerate=self.samplerate,
            pitch_threshold=self.pitch_threshold,
            amp_threshold=self.amp_threshold,
        )

        def callback(indata, frames, time, status):
            if status:
                print(status, flush=True)
            samples = indata[:, self.input_channel].copy()
            processor.process_block(samples)

        with sd.InputStream(
            device=self.device,
            channels=self.input_channel + 1,
            callback=callback,
            blocksize=self.buffer_size,
            samplerate=self.samplerate,
        ):
            while not self._stop_event.is_set():
                sd.sleep(100)
            processor.close()


class MidiLineGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MidiLine')
        self.worker = None
        layout = QVBoxLayout()

        # Device selection
        dev_layout = QHBoxLayout()
        dev_layout.addWidget(QLabel('Dispositivo'))
        self.device_combo = QComboBox()
        for idx, dev in enumerate(sd.query_devices()):
            if dev['max_input_channels'] > 0:
                self.device_combo.addItem(f"{idx}: {dev['name']}", idx)
        dev_layout.addWidget(self.device_combo)
        layout.addLayout(dev_layout)

        # Channel selection
        ch_in_layout = QHBoxLayout()
        ch_in_layout.addWidget(QLabel('Canal de entrada'))
        self.input_channel_combo = QComboBox()
        for ch in range(1, 9):
            self.input_channel_combo.addItem(str(ch), ch - 1)
        ch_in_layout.addWidget(self.input_channel_combo)
        layout.addLayout(ch_in_layout)

        # Buffer size dropdown
        buf_layout = QHBoxLayout()
        buf_layout.addWidget(QLabel('Buffer (samples)'))
        self.buffer_combo = QComboBox()
        for size in [64, 128, 256, 512]:
            self.buffer_combo.addItem(f"{size}", size)
        self.buffer_combo.setCurrentIndex(2)
        buf_layout.addWidget(self.buffer_combo)
        layout.addLayout(buf_layout)

        # Amplitude threshold slider
        amp_layout = QHBoxLayout()
        amp_layout.addWidget(QLabel('Amplitud [1-10]%'))
        self.amp_slider = QSlider(Qt.Horizontal)
        self.amp_slider.setRange(1, 100)
        self.amp_slider.setValue(1)
        self.amp_slider.setToolTip('Umbral minimo de amplitud para detectar notas')
        amp_layout.addWidget(self.amp_slider)
        self.amp_value = QLabel('1')
        self.amp_slider.valueChanged.connect(lambda v: self.amp_value.setText(str(v)))
        amp_layout.addWidget(self.amp_value)
        layout.addLayout(amp_layout)


        # Sample rate dropdown
        sr_layout = QHBoxLayout()
        sr_layout.addWidget(QLabel('SampleRate (Hz)'))
        self.sr_combo = QComboBox()
        self.sr_combo.addItem('44100', 44100)
        self.sr_combo.addItem('48000', 48000)
        sr_layout.addWidget(self.sr_combo)
        layout.addLayout(sr_layout)


        # MIDI port name
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel('Puerto'))
        self.port_edit = QLineEdit('MidiLine')
        port_layout.addWidget(self.port_edit)
        layout.addLayout(port_layout)


        self.setLayout(layout)
        # Adjust initial size and reduce width by 20%
        self.adjustSize()
        self.resize(int(self.width() * 0.8), self.height())

        # Start recording automatically
        self._start_recorder()

    def _start_recorder(self) -> None:
        """Initialize and start the recording thread."""
        device = self.device_combo.currentData()
        buffer_size = self.buffer_combo.currentData()
        amp_threshold = self.amp_slider.value() / 100.0
        samplerate = self.sr_combo.currentData()
        port = self.port_edit.text()
        input_channel = self.input_channel_combo.currentData()
        self.worker = RecorderThread(
            device,
            buffer_size,
            port,
            amp_threshold,
            0.1,
            samplerate=samplerate,
            input_channel=input_channel,
        )
        self.worker.start()

    def closeEvent(self, event):
        if self.worker and self.worker.is_alive():
            self.worker.stop()
            self.worker.join()
        event.accept()


def main():
    app = QApplication(sys.argv)
    gui = MidiLineGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
