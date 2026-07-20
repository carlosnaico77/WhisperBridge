# TRANSMISOR DE MICROFONO / MICROPHONE TRANSMITTER
## Informe de Desarrollo y Retos Técnicos / Development & Technical Challenges Report

---

# 🇪🇸 VERSIÓN EN ESPAÑOL

## 🏆 Logros Alcanzados en esta Sesión

1. **Arquitectura OOP Desacoplada (Multihilo)**:
   * Reestructuramos el script monolítico en 4 clases modulares que se comunican de forma asíncrona a través de colas (`Queue`):
     * [MicBridge](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/bridge.py): Capturador del micrófono físico.
     * [MicProcessor](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/processor.py): Traductor e interfaz con APIs (Groq + Edge-TTS).
     * [MicPlayer](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/player.py): Reproductor de audio sobre la tubería virtual PulseAudio (`Virtual_Mic`).
     * [TransmitterInitiator](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/initiator.py): Coordinador principal de hilos y consola.
2. **Controlador Híbrido (Dual Mode)**:
   * Diseñamos un selector configurable en [main.py](file:///home/clozano/Proyectos/TraductorUbuntu/src/main.py#L22) para cambiar con una sola variable entre los modos `'manual'` (pulsar ENTER) y `'streaming'` (traducción continua por VAD).
3. **Sincronización Total de Consola (UX)**:
   * Implementamos banderas de estado (`is_processing` y `is_playing`) para bloquear ordenadamente la consola hasta que terminen las llamadas a la API y el sonido físico, eliminando por completo el solapamiento de textos en la terminal.
4. **Filtro de Silencios Monitores (Bug de Hardware)**:
   * Solucionamos la captura de silencio absoluto (`0.0000`) descartando los monitores virtuales de altavoz de PulseAudio mediante exclusión de la palabra clave `"monitor"`.

---

## 🔍 Retos Técnicos Identificados en Modo Streaming

El modo `'streaming'` (captura manos libres) presenta problemas de alucinación y de control debido a los siguientes factores:

### 1. Alucinaciones de Whisper con Silencio o Ruido
* **Síntoma**: Durante pausas largas o ruido de respiración, Whisper alucina palabras fijas como *"Thank you"*, *"I'm sorry"*, *"you"* o *"Bye"*.
* **Causa**: Whisper fue entrenado para transcribir y traducir voz activa. Cuando el búfer contiene solo ruido blanco o silencio, el modelo tiende a predecir los tokens más comunes de su corpus (agradecimientos y saludos).
* **Solución**: Reemplazar el detector RMS simple por un modelo de VAD neuronal local como **Silero VAD** o **WebRTC VAD** para discriminar perfectamente voz real de ruidos.

### 2. Bloqueo del Teclado al Pausar (`input()` síncrono)
* **Síntoma**: Al presionar `ENTER` para pausar el streaming automático, el sistema a veces no responde de inmediato.
* **Causa**: La función `input()` de Python es bloqueante y síncrona en el hilo principal. Si se presiona `ENTER` mientras los hilos secundarios envían logs, la cola de la terminal se retrasa.
* **Solución**: Usar atajos de teclado globales no bloqueantes a nivel de sistema operativo (como con la librería `pynput` o `keyboard`).

---
---

# 🇺🇸 ENGLISH VERSION

## 🏆 Achievements in this Session

1. **Decoupled OOP Architecture (Multi-threaded)**:
   * We refactored the monolithic script into 4 modular classes communicating asynchronously via thread-safe queues (`Queue`):
     * [MicBridge](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/bridge.py): Captures raw audio from the physical microphone.
     * [MicProcessor](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/processor.py): Translates and interfaces with APIs (Groq + Edge-TTS).
     * [MicPlayer](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/player.py): Plays translated audio on the PulseAudio virtual mic pipe (`Virtual_Mic`).
     * [TransmitterInitiator](file:///home/clozano/Proyectos/TraductorUbuntu/src/services/transmisor/initiator.py): Orchestrates queues, background threads, and terminal input.
2. **Hybrid Controller (Dual Mode)**:
   * Designed a simple configuration selector in [main.py](file:///home/clozano/Proyectos/TraductorUbuntu/src/main.py#L22) to switch with a single variable between `'manual'` (press ENTER to speak) and `'streaming'` (continuous VAD translation).
3. **Console Synchronization (UX)**:
   * Implemented status flags (`is_processing` and `is_playing`) to hold the main thread prompt until API requests and audio playbacks finish, avoiding overlapping logs in the terminal.
4. **Output Monitor Filter (Hardware Bug)**:
   * Solved a silent capture bug (`0.0000` amplitude) by excluding PulseAudio speaker loopbacks using a `"monitor"` string rejection filter.

---

## 🔍 Technical Challenges in Streaming Mode

The `'streaming'` mode (hands-free capture) shows two main limitations:

### 1. Whisper Hallucinations during Silence/Noise
* **Symptom**: During long pauses or breathing, Whisper hallucinates static phrases like *"Thank you"*, *"I'm sorry"*, *"you"*, or *"Bye"*.
* **Cause**: Whisper was trained on active voice data. When the input buffer contains only noise or silence, the model shifts its prediction probabilities toward the most common tokens in its training dataset.
* **Solution**: Replace the simple RMS amplitude gate with a local neural Voice Activity Detector (VAD) like **Silero VAD** or **WebRTC VAD** to properly filter speech from environment noise.

### 2. Keyboard Input Blocking (`input()` blocking)
* **Symptom**: Pressing `ENTER` to pause the automatic streaming mode does not always stop the stream instantly.
* **Cause**: Python's `input()` function is synchronous and blocks the stdout/stdin main thread.
* **Solution**: Implement non-blocking system-level hotkeys (using libraries like `pynput` or `keyboard`) to activate/pause the listener cleanly.
