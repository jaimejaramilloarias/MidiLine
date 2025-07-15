# Arquitectura Base de MidiLine

MidiLine es una aplicación modular diseñada inicialmente para la detección de audio monofónico de guitarra y la conversión a MIDI. La estructura propuesta facilita la futura expansión a procesamiento polifónico.

## 1. Módulo de Entrada de Audio
- **Objetivo:** Capturar audio desde una interfaz de audio local.
- **Implementación inicial:** Utilizar una biblioteca multiplataforma como PortAudio para manejar distintos drivers (ASIO/ALSA/CoreAudio).
- **Expansión futura:** Soporte para multicanal si se desea procesar entrada estéreo o varias fuentes.

- **Normalización y filtrado:** Ajuste de ganancia y filtrado de ruidos (por ejemplo, un filtro paso alto ajustable que elimina frecuencias por debajo de 40 Hz).
- **Segmentación en bloques:** División de la señal en ventanas solapadas (p. ej., 2048 o 4096 muestras) para análisis en tiempo real.

## 3. Detección de Pitch (Monofónico)
- **Algoritmo base:** Implementar YIN o autocorrelación, adecuados para una sola fuente.
- **Suavizado:** Aplicar filtros medianos o de seguimiento para reducir variaciones abruptas.
- **Preparación para polifonía:** Definir una interfaz que permita reemplazar fácilmente este módulo por uno multi‑pitch en versiones futuras.

## 4. Manejo de Eventos Musicales
- **Onset/Offset:** Detectar el inicio y final de cada nota a partir de cambios en la energía o en el pitch detectado.
- **Duración y velocidad:** Calcular la duración de la nota y asignar una “velocity” según la amplitud.

## 5. Generación de Mensajes MIDI
- **Conversión:** Mapear las frecuencias a números de nota MIDI.
- **Envío:** Utilizar una biblioteca como RtMidi o mido para transmitir NoteOn y NoteOff a un puerto MIDI virtual.
- **Latencia:** Mantener el tiempo de procesamiento por debajo de 20–30 ms para uso en tiempo real.

## 6. Interfaz de Usuario
- **Inicialmente:** Consola o línea de comandos para seleccionar la interfaz de audio y configurar parámetros.
- **Posteriormente:** Posible GUI que permita visualizar la actividad y ajustar opciones.

## 7. Consideraciones para Polifonía
- **Modularidad:** Cada módulo (entrada, procesamiento, detección de pitch) expone interfaces claras para sustituir o ampliar componentes.
- **Escalabilidad:** El flujo de datos y la estructura de eventos deben contemplar múltiples notas simultáneas, aunque inicialmente solo se procese una.
- **Separación de fuentes:** En versiones polifónicas se añadirán algoritmos de separación (HPSS, NMF, modelos de aprendizaje profundo) antes de la detección de pitch.

## Esquema General
```
[Entrada de Audio] -> [Preprocesamiento] -> [Detección de Pitch] -> [Manejo de Eventos] -> [Salida MIDI]
```
Este flujo básico se mantendrá al incorporar la polifonía, añadiendo o reemplazando módulos según la complejidad requerida.

