# 🎙️ Implementation Guide: Outgoing Voice Translation (Virtual Microphone)

This document details the audio design, system configuration in Ubuntu, and the execution workflow to translate your own voice in real-time.

The goal is to speak Spanish into your physical microphone and have meeting participants (on Zoom, Teams, Meet) hear a highly natural synthesized voice in English.

---

## 🗺️ Audio Routing Architecture

To keep the system running without interference, we must physically isolate what your real microphone captures from what the meeting software hears.

![Flow Diagram](docs/mic_translation_flow.png)

---

## 🎛️ Audio Configuration in Ubuntu (Step-by-Step)

To prepare your operating system before running the code:

### 1. Create the Virtual Mic Channel (`Virtual_Mic`)
In your Ubuntu terminal, run the following command to create the audio bridge sink:
```bash
pactl load-module module-null-sink sink_name=Virtual_Mic sink_properties=device.description="Virtual_Mic"
```
*   This will create a virtual output device named `Virtual_Mic` and its corresponding monitor device (`Virtual_Mic.monitor`) which will act as your new virtual microphone.

### 2. Configure Zoom / Teams / Google Meet
Open your meeting software's audio configuration:
*   **Speakers (Output):** Set to your normal physical output (headphones or speakers) or the `Virtual_Cable` if you are also translating incoming audio.
*   **Microphone (Input):** Select **`Virtual_Mic`** (or **`Virtual_Mic.monitor`**). *Do not select your actual physical microphone.*

---

## 🚀 Isolated Development Plan

We will develop this functionality in a separate script (e.g., `src/services/mic_translator.py`) before integrating it into the system's main flow. The step-by-step process of this module is:

### Step 1: Local Voice Capture
*   Capture the input channel of your physical microphone using the `sounddevice` library.
*   Implement a recording trigger:
    *   **Option A (Push-to-Talk):** Record only while holding down a specific key (such as `Alt` or `Space`).
    *   **Option B (Silence Detection):** Record continuously and process the segment when a silence pause is detected.

### Step 2: Direct Translation with Groq API
*   Convert the recorded audio chunk into a temporary in-memory WAV file.
*   Call Groq's translations API endpoint:
    ```http
    POST https://api.groq.com/openai/v1/audio/translations
    ```
    *By using the `/translations` endpoint, Groq accepts Spanish audio and directly returns the translated English text transcript in a single step.*

### Step 3: Natural Voice Generation (Edge-TTS)
*   Use the `edge-tts` library to convert the translated English text from Groq into a highly natural human speech audio stream.

### Step 4: Playback on the Virtual Audio Pipe
*   Configure `sounddevice` to play the Edge-TTS audio stream, directing the output target specifically to the `Virtual_Mic` device.

---

## 📦 Additional Dependencies

Before coding, we will need to install these packages:
```bash
pip install edge-tts keyboard
```
*   `edge-tts`: To generate high-quality English human voice audio for free.
*   `keyboard`: To capture system-wide hotkeys (Push-to-Talk) at the operating system level.
