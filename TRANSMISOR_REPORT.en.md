# MICROPHONE TRANSMITTER
## Development & Technical Challenges Report

---

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

## 🔍 Technical Challenges

### 1. Bidirectional Concurrency: Unifying Receiver & Transmitter (Next Step!)
* **The Problem**: Currently, the **Incoming Channel (Receiver)** (to listen/translate others) and the **Outgoing Channel (Transmitter)** (to speak by pressing ENTER) are separated and commented out in `main.py`. The console user interface of both streams would conflict if they tried to capture keyboard input or print logs concurrently.
* **The Challenge**: Design an orchestrator that runs both services simultaneously in separate threads without blocking one another.
* **Action Line**:
  * Run the audio receiver silently in a background thread (listening to `Virtual_Cable.monitor` and outputting text).
  * Keep the transmitter's keyboard interaction loop (`ENTER` keypresses) in the main thread.
  * Design a unified CLI dashboard to show incoming translation logs alongside transmitter status.

### 2. Whisper Hallucinations during Silence/Noise (Streaming Mode)
* **Symptom**: During long pauses or breathing, Whisper hallucinates static phrases like *"Thank you"*, *"I'm sorry"*, *"you"*, or *"Bye"*.
* **Cause**: Whisper was trained on active voice data. When the input buffer contains only noise or silence, the model shifts its prediction probabilities toward the most common tokens in its training dataset.
* **Solution**: Replace the simple RMS amplitude gate with a local neural Voice Activity Detector (VAD) like **Silero VAD** or **WebRTC VAD** to properly filter speech from environment noise.

### 3. Keyboard Input Blocking (`input()` blocking in Streaming Mode)
* **Symptom**: Pressing `ENTER` to pause the automatic streaming mode does not always stop the stream instantly.
* **Cause**: Python's `input()` function is synchronous and blocks the stdout/stdin main thread.
* **Solution**: Implement non-blocking system-level hotkeys (using libraries like `pynput` or `keyboard`) to activate/pause the listener cleanly.
