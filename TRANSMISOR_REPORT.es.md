# TRANSMISOR DE MICROFONO
## Informe de Desarrollo y Retos Técnicos

---

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

## 🔍 Retos Técnicos Identificados

### 1. Concurrencia Bidireccional: Unificar Receptor y Transmisor (¡Próximo Paso!)
* **El Problema**: Actualmente, el **Canal Entrante (Receptor)** (para escuchar a los demás) y el **Canal Saliente (Transmisor)** (para hablar en inglés al pulsar ENTER) están separados y comentados en `main.py`. El flujo principal de consola del receptor de audio y el del transmisor entrarían en conflicto si intentan capturar el teclado o imprimir logs al mismo tiempo.
* **El Reto**: Diseñar un orquestador que permita ejecutar ambos servicios de manera simultánea en hilos independientes sin bloquearse mutuamente.
* **Línea de Acción**:
  * Lanzar el receptor de audio en un hilo de fondo (escuchando `Virtual_Cable.monitor` de manera silenciosa en texto en consola o pantalla).
  * Mantener el hilo de control manual por `ENTER` del transmisor en primer plano.
  * Diseñar una interfaz unificada en consola que muestre la transcripción de la videollamada en paralelo al control de tu micrófono.

### 2. Alucinaciones de Whisper con Silencio o Ruido (Modo Streaming)
* **Síntoma**: Durante pausas largas o ruido de respiración, Whisper alucina palabras fijas como *"Thank you"*, *"I'm sorry"*, *"you"* o *"Bye"*.
* **Causa**: Whisper fue entrenado para transcribir y traducir voz activa. Cuando el búfer contiene solo ruido blanco o silencio, el modelo tiende a predecir los tokens más comunes de su corpus.
* **Solución**: Reemplazar el detector RMS simple por un modelo de VAD neuronal local como **Silero VAD** o **WebRTC VAD** para discriminar perfectamente voz real de ruidos.

### 3. Bloqueo del Teclado al Pausar (`input()` síncrono en Streaming)
* **Síntoma**: Al presionar `ENTER` para pausar el streaming automático, el sistema a veces no responde de inmediato.
* **Causa**: La función `input()` de Python es bloqueante y síncrona en el hilo principal. Si se presiona `ENTER` mientras los hilos secundarios envían logs, la cola de la terminal se retrasa.
* **Solución**: Usar atajos de teclado globales no bloqueantes a nivel de sistema operativo (como con la librería `pynput` o `keyboard`).
