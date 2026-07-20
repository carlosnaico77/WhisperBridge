# services/transmisor/mic_translator.py
import os
import io
import wave
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd
# pyrefly: ignore [missing-import]
import soundfile as sf
import requests
import asyncio
# pyrefly: ignore [missing-import]
import edge_tts

# Códigos de color ANSI para la terminal
class ColoresConsola:
    VERDE = '\033[92m'
    CIAN = '\033[96m'
    AMARILLO = '\033[93m'
    BLANCO_NEGRITA = '\033[1m'
    GRIS = '\033[90m'
    ROJO = '\033[91m'
    RESET = '\033[0m'

def load_env():
    """Carga variables del archivo .env en la raíz del proyecto."""
    env_path = ".env"
    if not os.path.exists(env_path) and os.path.exists("../../../.env"):
        env_path = "../../../.env"
    elif not os.path.exists(env_path) and os.path.exists("../../.env"):
        env_path = "../../.env"

    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

class MicTranslator:
    def __init__(self):
        self.samplerate = 16000
        self.channels = 1
        self.recording = []
        self.is_recording = False
        self.stream = None

    def find_devices(self):
        """Busca el micrófono USB y el canal Virtual_Mic en sounddevice."""
        devices = sd.query_devices()
        mic_idx = None
        output_idx = None

        for idx, d in enumerate(devices):
            if "GeneralPlus" in d['name'] and d['max_input_channels'] > 0:
                mic_idx = idx
            if "Virtual_Mic" in d['name'] and d['max_output_channels'] > 0:
                output_idx = idx

        # Fallbacks
        if mic_idx is None:
            mic_idx = sd.default.device[0]
        if output_idx is None:
            for idx, d in enumerate(devices):
                if "Virtual_Mic" in d['name'] and d['max_output_channels'] > 0:
                    output_idx = idx
                    break
            if output_idx is None:
                output_idx = sd.default.device[1]

        return mic_idx, output_idx

    def _audio_callback(self, indata, frames, time, status):
        """Callback asíncrono para almacenar los bloques de audio capturados."""
        if self.is_recording:
            self.recording.append(indata.copy())

    def start_recording(self, mic_idx):
        """Inicia la grabación en un flujo de fondo."""
        self.recording = []
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            device=mic_idx,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop_recording(self):
        """Detiene el flujo de grabación y retorna el array de audio completo."""
        if self.stream:
            self.is_recording = False
            self.stream.stop()
            self.stream.close()
            self.stream = None
        if len(self.recording) > 0:
            return np.concatenate(self.recording, axis=0)
        return np.array([], dtype=np.float32)

    def translate_audio(self, audio_data) -> str:
        """Envía el audio a la API de traducción de Groq (ES➔EN)."""
        token = os.environ.get("GROGTOKEN", "")
        if not token:
            print(f"{ColoresConsola.ROJO}[ERROR]: No se encontró GROGTOKEN en el archivo .env{ColoresConsola.RESET}")
            return ""

        audio_int16 = (audio_data * 32767).astype(np.int16)
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.samplerate)
            wav_file.writeframes(audio_int16.tobytes())
        wav_io.seek(0)

        headers = {
            "Authorization": f"Bearer {token}"
        }
        files = {
            "file": ("audio.wav", wav_io, "audio/wav")
        }
        data = {
            "model": "whisper-large-v3",
            "response_format": "json"
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/translations",
                headers=headers,
                files=files,
                data=data,
                timeout=15
            )
            if response.status_code == 200:
                return response.json().get("text", "").strip()
            else:
                print(f"{ColoresConsola.ROJO}[API ERROR {response.status_code}]: {response.text}{ColoresConsola.RESET}")
                return ""
        except Exception as e:
            print(f"{ColoresConsola.ROJO}[API EXCEPTION]: {e}{ColoresConsola.RESET}")
            return ""

    async def synthesize_voice(self, text: str, output_file="temp.mp3"):
        """Sintetiza texto en inglés a un archivo de voz usando edge-tts."""
        voice = "en-US-AndrewNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)

def iniciar_traduccion_mic():
    """Ejecuta el bucle de traducción de micrófono virtual de forma interactiva."""
    print(f"\n{ColoresConsola.CIAN}╔══════════════════════════════════════════════════════════╗{ColoresConsola.RESET}")
    print(f"{ColoresConsola.CIAN}║       PROTOTIPO: TRADUCTOR DE MICRÓFONO (VIRTUAL MIC)    ║{ColoresConsola.RESET}")
    print(f"{ColoresConsola.CIAN}╚══════════════════════════════════════════════════════════╝{ColoresConsola.RESET}")

    translator = MicTranslator()
    mic_idx, output_idx = translator.find_devices()
    
    devices = sd.query_devices()
    print(f"{ColoresConsola.VERDE}▶ Micrófono de entrada:  {ColoresConsola.BLANCO_NEGRITA}{devices[mic_idx]['name']} (Index {mic_idx}){ColoresConsola.RESET}")
    print(f"{ColoresConsola.VERDE}▶ Tubería de salida:      {ColoresConsola.BLANCO_NEGRITA}{devices[output_idx]['name']} (Index {output_idx}){ColoresConsola.RESET}")
    print(f"{ColoresConsola.CIAN}────────────────────────────────────────────────────────────{ColoresConsola.RESET}\n")

    try:
        while True:
            input(f"{ColoresConsola.AMARILLO}👉 Presiona ENTER para empezar a hablar (Habla en Español)...{ColoresConsola.RESET}")
            translator.start_recording(mic_idx)
            
            input(f"{ColoresConsola.VERDE}🎤 Grabando... Presiona ENTER para detener y procesar...{ColoresConsola.RESET}")
            audio_data = translator.stop_recording()
            
            if len(audio_data) == 0:
                print(f"{ColoresConsola.ROJO}No se capturó audio.{ColoresConsola.RESET}\n")
                continue

            print(f"{ColoresConsola.AMARILLO}Traduciendo voz con Groq Cloud (ES ➔ EN)...{ColoresConsola.RESET}")
            english_text = translator.translate_audio(audio_data)
            
            if not english_text:
                print(f"{ColoresConsola.ROJO}Error en la traducción.{ColoresConsola.RESET}\n")
                continue
                
            print(f"{ColoresConsola.CIAN}📝 [TRADUCCIÓN AL INGLÉS]:{ColoresConsola.RESET} {ColoresConsola.BLANCO_NEGRITA}{english_text}{ColoresConsola.RESET}")

            print(f"{ColoresConsola.AMARILLO}Generando voz humana (Edge-TTS)...{ColoresConsola.RESET}")
            asyncio.run(translator.synthesize_voice(english_text, "temp.mp3"))

            # Convertimos MP3 a WAV de forma limpia usando ffmpeg
            os.system("ffmpeg -y -i temp.mp3 temp.wav >/dev/null 2>&1")

            if os.path.exists("temp.wav"):
                print(f"{ColoresConsola.VERDE}🔊 Inyectando voz traducida en Virtual_Mic...{ColoresConsola.RESET}")
                
                # Usamos paplay nativo de Linux que gestiona y despierta automáticamente la tubería virtual
                os.system(f"paplay --device=Virtual_Mic temp.wav")
                
                print(f"{ColoresConsola.GRIS}Listo para la siguiente frase.{ColoresConsola.RESET}\n")
                
                os.remove("temp.mp3")
                os.remove("temp.wav")
            else:
                print(f"{ColoresConsola.ROJO}Error al generar el archivo de voz temporal.{ColoresConsola.RESET}\n")

    except KeyboardInterrupt:
        print("\nApagando prototipo de micrófono...")

if __name__ == "__main__":
    iniciar_traduccion_mic()
