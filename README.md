# MidiLine

MidiLine es una aplicación de línea de comandos que convierte audio monofónico en
mensajes MIDI en tiempo real. Permite abrir un puerto MIDI virtual y enviar las
notas detectadas a otras aplicaciones.

Desde la versión 0.2 cuenta además con una interfaz gráfica (GUI) que
ofrece diales y deslizadores para controlar todos los parámetros del
proceso de conversión de audio a MIDI.

## Instalación

Se recomienda utilizar un entorno virtual. Desde la raíz del repositorio
instala el paquete con:

```bash
pip install .
```

Esto instalará todas las dependencias y habilitará el comando `midiline`.

Consulta `docs/install_mac.md` para ver un ejemplo de instalación en macOS.

## Uso

El comando principal es `record`, que abre un puerto MIDI virtual y comienza a
escuchar el dispositivo de entrada.

```bash
midiline record --input-device 1 --buffer-size 1024 --midi-port MidiLine
```

- `--input-device` ID o nombre del dispositivo de entrada de audio.
- `--buffer-size` tamaño de la ventana de procesamiento (en muestras).
- `--midi-port` nombre del puerto MIDI donde se enviarán las notas.
- `--amp-threshold` umbral de amplitud para filtrar el ruido (0-1).
- `--tolerance` tolerancia para la detección de tono (0-1).

Presiona `Ctrl+C` para detener la grabación.

### Interfaz gráfica

Ejecuta la GUI con:

```bash
python -m midiline.gui
```

Desde ella puedes seleccionar el dispositivo de entrada y ajustar parámetros
de forma avanzada. La ventana incluye diales para el tamaño de buffer,
la frecuencia de corte del filtro paso alto, la velocidad y el canal MIDI,
así como controles para la tasa de muestreo, tamaño de frame y
umbral de silencio.

## Pruebas

Para ejecutar la suite de pruebas utiliza:

```bash
pytest
```
