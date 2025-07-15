import sys
import threading
import numpy as np
import sounddevice as sd
from .realtime import RealTimeProcessor
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDial,
    QSlider,
    QPushButton,
    QComboBox,
    QLineEdit,
    QCheckBox,
)
from PyQt5.QtCore import Qt


class RecorderThread(threading.Thread):
    def __init__(
        self,
        device,
        buffer_size,
        midi_port,
        amp_threshold,
        tolerance,
        samplerate=44100,
        frame_size=None,
        cutoff=None,
        velocity=64,
        channel=0,
        silence=-40,
        gate_threshold=0.0,
        gate_attack=2,
        gate_release=10,
        debug=False,
    ):
        super().__init__(daemon=True)
        self.device = device
        self.buffer_size = buffer_size
        self.frame_size = frame_size or buffer_size * 2
        self.samplerate = samplerate
        self.midi_port = midi_port
        self.amp_threshold = amp_threshold
        self.tolerance = tolerance
        self.cutoff = cutoff
        self.velocity = int(velocity)
        self.channel = int(channel)
        self.silence = silence
        self.gate_threshold = gate_threshold
        self.gate_attack = gate_attack
        self.gate_release = gate_release
        self.debug = debug
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        processor = RealTimeProcessor(
            midi_port=self.midi_port,
            buffer_size=self.buffer_size,
            samplerate=self.samplerate,
            tolerance=self.tolerance,
            amp_threshold=self.amp_threshold,
            cutoff=self.cutoff,
            history_size=5,
            velocity=self.velocity,
            channel=self.channel,
            gate_threshold=self.gate_threshold,
            gate_attack=self.gate_attack,
            gate_release=self.gate_release,
            silence=self.silence,
            debug=self.debug,
        )

        def callback(indata, frames, time, status):
            if status:
                print(status, flush=True)
            samples = np.frombuffer(indata, dtype=np.float32)
            processor.process_block(samples)

        with sd.InputStream(
            device=self.device,
            channels=1,
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
        amp_layout.addWidget(QLabel('Amplitud (%)'))
        self.amp_slider = QSlider(Qt.Horizontal)
        self.amp_slider.setRange(1, 100)
        self.amp_slider.setValue(1)
        amp_layout.addWidget(self.amp_slider)
        layout.addLayout(amp_layout)

        # Noise gate threshold slider
        gate_layout = QHBoxLayout()
        gate_layout.addWidget(QLabel('NoiseGate (%)'))
        self.gate_slider = QSlider(Qt.Horizontal)
        self.gate_slider.setRange(0, 100)
        self.gate_slider.setValue(0)
        gate_layout.addWidget(self.gate_slider)
        layout.addLayout(gate_layout)

        gate_time = QHBoxLayout()
        gate_time.addWidget(QLabel('Ataque (frames)'))
        self.gate_attack_dial = QDial()
        self.gate_attack_dial.setRange(1, 20)
        self.gate_attack_dial.setValue(2)
        self.gate_attack_dial.setNotchesVisible(True)
        gate_time.addWidget(self.gate_attack_dial)
        gate_time.addWidget(QLabel('Release (frames)'))
        self.gate_release_dial = QDial()
        self.gate_release_dial.setRange(1, 50)
        self.gate_release_dial.setValue(10)
        self.gate_release_dial.setNotchesVisible(True)
        gate_time.addWidget(self.gate_release_dial)
        layout.addLayout(gate_time)

        # Tolerance slider
        tol_layout = QHBoxLayout()
        tol_layout.addWidget(QLabel('Tolerancia (%)'))
        self.tol_slider = QSlider(Qt.Horizontal)
        self.tol_slider.setRange(50, 100)
        self.tol_slider.setValue(80)
        tol_layout.addWidget(self.tol_slider)
        layout.addLayout(tol_layout)

        # Sample rate dropdown
        sr_layout = QHBoxLayout()
        sr_layout.addWidget(QLabel('SampleRate (Hz)'))
        self.sr_combo = QComboBox()
        self.sr_combo.addItem('44100', 44100)
        self.sr_combo.addItem('48000', 48000)
        sr_layout.addWidget(self.sr_combo)
        layout.addLayout(sr_layout)

        # Frame size knob
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel('Frame (samples)'))
        self.frame_dial = QDial()
        self.frame_dial.setRange(512, 4096)
        self.frame_dial.setValue(2048)
        self.frame_dial.setNotchesVisible(True)
        frame_layout.addWidget(self.frame_dial)
        layout.addLayout(frame_layout)

        # Low-pass cutoff knob
        cutoff_layout = QHBoxLayout()
        cutoff_layout.addWidget(QLabel('LowPass (Hz)'))
        self.cutoff_dial = QDial()
        self.cutoff_dial.setRange(1000, 12000)
        self.cutoff_dial.setValue(6000)
        self.cutoff_dial.setNotchesVisible(True)
        cutoff_layout.addWidget(self.cutoff_dial)
        layout.addLayout(cutoff_layout)

        # Velocity knob
        vel_layout = QHBoxLayout()
        vel_layout.addWidget(QLabel('Velocidad (1-127)'))
        self.velocity_dial = QDial()
        self.velocity_dial.setRange(1, 127)
        self.velocity_dial.setValue(64)
        self.velocity_dial.setNotchesVisible(True)
        vel_layout.addWidget(self.velocity_dial)
        layout.addLayout(vel_layout)

        # Channel knob
        ch_layout = QHBoxLayout()
        ch_layout.addWidget(QLabel('Canal (0-15)'))
        self.channel_dial = QDial()
        self.channel_dial.setRange(0, 15)
        self.channel_dial.setValue(0)
        self.channel_dial.setNotchesVisible(True)
        ch_layout.addWidget(self.channel_dial)
        layout.addLayout(ch_layout)

        # Silence slider
        silence_layout = QHBoxLayout()
        silence_layout.addWidget(QLabel('Silencio (dB)'))
        self.silence_slider = QSlider(Qt.Horizontal)
        self.silence_slider.setRange(0, 80)
        self.silence_slider.setValue(40)
        silence_layout.addWidget(self.silence_slider)
        layout.addLayout(silence_layout)

        # MIDI port name
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel('Puerto'))
        self.port_edit = QLineEdit('MidiLine')
        port_layout.addWidget(self.port_edit)
        layout.addLayout(port_layout)

        # Debug checkbox
        self.debug_check = QCheckBox('Debug')
        layout.addWidget(self.debug_check)

        # Start/Stop button
        self.btn = QPushButton('Iniciar')
        self.btn.clicked.connect(self.toggle_record)
        layout.addWidget(self.btn)

        self.setLayout(layout)
        # Adjust initial size and reduce width by 20%
        self.adjustSize()
        self.resize(int(self.width() * 0.8), self.height())

    def toggle_record(self):
        if self.worker and self.worker.is_alive():
            self.worker.stop()
            self.worker.join()
            self.worker = None
            self.btn.setText('Iniciar')
        else:
            device = self.device_combo.currentData()
            buffer_size = self.buffer_combo.currentData()
            amp_threshold = self.amp_slider.value() / 100.0
            tolerance = self.tol_slider.value() / 100.0
            samplerate = self.sr_combo.currentData()
            frame_size = self.frame_dial.value()
            cutoff = self.cutoff_dial.value()
            velocity = self.velocity_dial.value()
            channel = self.channel_dial.value()
            silence = -float(self.silence_slider.value())
            gate_threshold = self.gate_slider.value() / 100.0
            gate_attack = self.gate_attack_dial.value()
            gate_release = self.gate_release_dial.value()
            port = self.port_edit.text()
            debug = self.debug_check.isChecked()
            self.worker = RecorderThread(
                device,
                buffer_size,
                port,
                amp_threshold,
                tolerance,
                samplerate=samplerate,
                frame_size=frame_size,
                cutoff=cutoff,
                velocity=velocity,
                channel=channel,
                silence=silence,
                gate_threshold=gate_threshold,
                gate_attack=gate_attack,
                gate_release=gate_release,
                debug=debug,
            )
            self.worker.start()
            self.btn.setText('Detener')


def main():
    app = QApplication(sys.argv)
    gui = MidiLineGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
