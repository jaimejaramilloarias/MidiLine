import click
import sounddevice as sd
import numpy as np
from realtime import RealTimeProcessor

@click.group()
def cli():
    """Herramienta de línea de comandos para MidiLine."""
    pass

@cli.command()
@click.option('--input-device', default=None, help='ID o nombre del dispositivo de entrada')
@click.option('--buffer-size', default=1024, type=int, help='Tamaño del bloque de audio')
@click.option('--midi-port', default='MidiLine', help='Puerto MIDI de salida')
@click.option('--input-channel', default=1, type=int, help='Canal del dispositivo de entrada (1-n)')
@click.option('--midi-channel', default=1, type=int, help='Canal MIDI (1-16)')
@click.option('--amp-threshold', default=0.01, type=float,
              help='Umbral de amplitud para detectar notas')
@click.option('--tolerance', default=0.8, type=float,
              help='Tolerancia de detección de tono (aubio)')
def record(input_device, buffer_size, midi_port, input_channel, midi_channel, amp_threshold, tolerance):
    """Captura audio y envía notas MIDI en tiempo real."""
    samplerate = 44100
    processor = RealTimeProcessor(
        midi_port=midi_port,
        buffer_size=buffer_size,
        samplerate=samplerate,
        tolerance=tolerance,
        amp_threshold=amp_threshold,
        channel=midi_channel - 1,
    )

    def callback(indata, frames, time, status):
        if status:
            print(status, flush=True)
        samples = indata[:, input_channel - 1].copy()
        processor.process_block(samples)

    with sd.InputStream(
        device=input_device,
        channels=input_channel,
        callback=callback,
        blocksize=buffer_size,
        samplerate=samplerate,
    ):
        click.echo('Grabando... Presiona Ctrl+C para detener')
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            pass
        finally:
            processor.close()
            click.echo('Grabación finalizada')

if __name__ == '__main__':
    cli()
