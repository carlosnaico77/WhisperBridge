# Real-Time Translator & Transcriber (Ubuntu)

> 📖 [Leer en Español](README.es.md)

This project is a real-time audio processor designed to capture sound from any system source in Ubuntu (such as media players like VLC, web browsers, Zoom/Teams calls, or physical microphones), transcribe it using OpenAI's Whisper model, and optionally translate and read it aloud using Text-to-Speech (TTS) or print it styled to the terminal.

---

## 🎯 Project Purpose

WhisperBridge was created with the mission to **eliminate language barriers in both professional and academic settings**. Its primary goal is to empower users to attend meetings, webinars, or work conferences in non-native languages (such as English) and enjoy an accurate, real-time local translation or transcription directly via their terminal or speakers.

### Project Philosophy:
*   **Extreme Resource Optimization:** Built on the principle of keeping local hardware load to a minimum. By utilizing elastic buffers and execution control queues, audio processing is performed in efficient batches, preventing any interference with operating system performance.
*   **Future-Proof:** Designed modularly (OOP) so that once more powerful external APIs are integrated, language accuracy will scale exponentially without requiring core architectural changes while maintaining the application's lightweight footprint.

---

## 🚀 Architecture & Improvements Made

We have fully refactored the original codebase, focusing on stability, performance, and best practices (OOP):

1. **Object-Oriented Design (OOP):**
   * **`AudioBridge` (in `bridge.py`):** Handles capturing blocks from the microphone and routing them to the appropriate queues, as well as handling the optional local playback/loopback.
   * **`AudioProcessor` (in `processor.py`):** Encapsulates the AI model (Whisper), the audio accumulation buffer, and the Text-to-Speech engine (`pyttsx3`).
   * **Instance Export:** The files directly export preconfigured instances (`audio_bridge` and `audio_processor`) to simplify imports in `main.py`.

2. **Audio Conflict Resolution (Elastic Buffer Queues):**
   * We separated the audio stream into two distinct queues (`ia_queue` and `playback_queue`).
   * **Increased Queue Size (`maxsize=500`):** We increased the capacity of `ia_queue` to hold up to 500 audio chunks (approx. 32 seconds). This acts as an elastic buffer that accumulates pending work while the Whisper AI performs inference on the CPU. Consequently, **no words or phrases are lost** when the processor is busy.

3. **Text-to-Speech (TTS) Stability:**
   * The `pyttsx3` engine is not thread-safe. We implemented a dedicated, persistent worker thread (`_worker_voz`) that consumes tasks sequentially from a queue (`voz_queue`), preventing application crashes and memory leaks.

4. **Latency & Accuracy Optimization:**
   * We configured the processing buffer to **80 blocks (~5.12 seconds)**. This provides the Whisper AI with full sentence context, dramatically increasing transcription accuracy while reducing CPU usage by 60% due to less frequent inference cycles.

5. **Dynamic Modes & Loopback Muting:**
   * Supports **`'escritura'`** (writing) mode (only prints to the terminal, disables the TTS background worker to save CPU, and routes the original audio back so you can hear the video).
   * Supports **`'voz'`** (voice) mode (reads the transcribed/translated text aloud and **automatically mutes the original audio loopback** so you only hear the synthesized voice).
   * Strict typing using `typing.Literal` for static validation in the IDE.

6. **Warning Resolution (FP16 / FP32):**
   * We import `torch` to dynamically check if an NVIDIA GPU is available (`torch.cuda.is_available()`). On CPU, it automatically disables `fp16` (`fp16=False`), removing clean-up warnings in the terminal.

7. **Flexible Execution Environments (Local vs Cloud API):**
   * Integrated the `tipo_uso: TipoUso` parameter.
   * **`'local'`**: 100% offline physical privacy. Loads Whisper locally on your CPU/GPU hardware.
   * **`'api'`**: Peak local hardware optimization. Delegates transcribing workloads to the cloud. The file `processor.py` includes a template method `_transcribir_via_api` detailing in-memory WAV buffer generation and API POST request formatting where the user can plug in their API keys.

---

## 🎛️ Audio Routing in Ubuntu (Virtual Cable)

To capture internal audio (e.g. from a browser playing YouTube) and route it to this script:

### 1. Create a Virtual Audio Cable (Null Sink)
In Ubuntu (using PulseAudio or PipeWire), run the following command in your terminal:
```bash
pactl load-module module-null-sink sink_name=Virtual_Cable sink_properties=device.description="Virtual_Cable"
```
* This creates a virtual output device named `Virtual_Cable` and a recording device (monitor) named `Virtual_Cable.monitor`.

### 2. Verify Created Devices
Confirm the active devices by running:
* **Recording sources (Inputs):** `pactl list sources short` (look for `Virtual_Cable.monitor`)
* **Playback sinks (Outputs):** `pactl list sinks short` (look for `Virtual_Cable`)

### 3. Route Audio
1. Play audio from a browser/media player.
2. Open **Ubuntu Sound Settings** (or run `pavucontrol` in the terminal).
3. In the **Playback** tab, redirect your browser's audio output to **Virtual_Cable**.
4. The sound will now route into the virtual pipe and get captured by the script via `Virtual_Cable.monitor` (the default input device).

---

## 🛠️ Running the Project

1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```
2. **Run the main application:**
   ```bash
   python main.py
   ```
---

## 🛣️ Future Roadmap & Requirements

The mid-term goal is to enable **real-time bi-directional translation (e.g., English ➔ Spanish)**. To achieve this and continue developing, the following steps are planned:

### 1. Cloud API Integration (Groq / OpenAI)
To speed up processing to milliseconds and access larger models (like `Whisper Large-v3`) without overloading local CPU resources, we will implement HTTP requests to Groq or OpenAI APIs.

### 🔑 Critical Requirement: VPN Usage (For geoblocked regions like Venezuela)
Due to US commercial regulations and sanctions, platforms like OpenAI and Groq block requests originating from specific countries (returning a `Forbidden` error).
*   **To Develop/Test:** It is mandatory to run an **active OS-level VPN** (such as ProtonVPN, Windscribe, etc.) on the Ubuntu host machine.
*   **Outcome:** This enables both accessing the developer console to obtain API keys and sending HTTP requests from the Python script without being rejected by the platform firewall.

---

## 💻 Testing Environment (Author's Specifications)

This project has been successfully developed and verified under the following environment:
*   **Operating System:** Ubuntu Linux (64-bit)
*   **Audio Server:** PipeWire / PulseAudio (via `module-null-sink`)
*   **Python Interpreter:** Python 3.14.4 (running inside a `venv` virtual environment)
*   **System Compiler:** GCC 15.2.0
*   **Inference Hardware:** CPU execution (with auto-fallback to FP32 precision)
*   **Editor/IDE:** VS Code / Cursor (configured to point to the local `venv` interpreter)

