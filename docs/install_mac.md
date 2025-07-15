# Instalación en macOS Catalina

Estas instrucciones asumen que tienes **Homebrew** instalado. Si no es así, instálalo desde https://brew.sh.

1. Instala las dependencias del sistema:
   ```bash
   brew install portaudio
   ```
2. Crea un entorno virtual de Python (3.10 o superior):
   ```bash
   python3 -m venv midiline-env
   source midiline-env/bin/activate
   pip install --upgrade pip
   ```
3. Instala MidiLine dentro del entorno:
   ```bash
   pip install -r requirements.txt  # o simplemente `pip install .`
   ```

Para ejecutar la aplicación desde la terminal:
```bash
midiline record --input-device 1
```
O para abrir la interfaz gráfica:
```bash
python -m midiline.gui
```

