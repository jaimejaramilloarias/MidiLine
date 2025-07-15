import click
import sounddevice as sd
import numpy as np
import aubio
import mido

@click.group()
def cli():
    """Herramienta de línea de comandos para MidiLine."""
    pass

@cli.command()
@click.option('--input-device', default=None, help='ID o nombre del dispositivo de entrada')
@click.option('--buffer-size', default=1024, type=int, help='Tamaño del bloque de audio')
@click.option('--midi-port', default='MidiLine', help='Puerto MIDI de salida')
@click.option('--amp-threshold', default=0.01, type=float,
              help='Umbral de amplitud para detectar notas')
@click.option('--tolerance', default=0.8, type=float,
              help='Tolerancia de detección de tono (aubio)')
def record(input_device, buffer_size, midi_port, amp_threshold, tolerance):
    """Captura audio y envía notas MIDI en tiempo real."""
    samplerate = 44100
    pitch_o = aubio.pitch('yin', buffer_size * 2, buffer_size, samplerate)
    pitch_o.set_unit('midi')
    pitch_o.set_silence(-40)
    pitch_o.set_tolerance(tolerance)
    try:
        out_port = mido.open_output(midi_port, virtual=True)
    except IOError:
        out_port = mido.open_output(midi_port)
    last_note = None

    def callback(indata, frames, time, status):
        nonlocal last_note
        if status:
            print(status, flush=True)
        samples = np.frombuffer(indata, dtype=np.float32)
        amplitude = float(np.sqrt(np.mean(samples ** 2)))
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()
        if (
            pitch > 0
            and amplitude > amp_threshold
            and confidence >= tolerance
        ):
            note = int(round(pitch))
            if note != last_note:
                if last_note is not None:
                    out_port.send(mido.Message('note_off', note=last_note, velocity=0))
                out_port.send(mido.Message('note_on', note=note, velocity=64))
                last_note = note

    with sd.InputStream(device=input_device, channels=1, callback=callback,
                         blocksize=buffer_size, samplerate=samplerate):
        click.echo('Grabando... Presiona Ctrl+C para detener')
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            pass
        finally:
            if last_note is not None:
                out_port.send(mido.Message('note_off', note=last_note, velocity=0))
            out_port.close()
            click.echo('Grabación finalizada')

if __name__ == '__main__':
    cli()
