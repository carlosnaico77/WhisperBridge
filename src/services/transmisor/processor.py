# services/transmisor/processor.py
import os
import io
import wave
# pyrefly: ignore [missing-import]
import numpy as np
import requests
import queue
import asyncio
# pyrefly: ignore [missing-import]
import edge_tts
from typing import Literal

# Definimos las mejores voces disponibles en inglés americano (US)
TipoVoz = Literal[
    'en-US-AndrewNeural',       # Masculino (Por defecto, profesional)
    'en-US-BrianNeural',        # Masculino (Grave, natural)
    'en-US-ChristopherNeural',  # Masculino (Conversacional)
    'en-US-EricNeural',         # Masculino (Corporativo)
    'en-US-EmmaNeural',         # Femenino (Claro, profesional)
    'en-US-AvaNeural',          # Femenino (Enérgico)
    'en-US-JennyNeural',        # Femenino (Nítido, estándar)
    'en-US-MichelleNeural'      # Femenino (Suave)
]

VOCES_DISPONIBLES = {
    "MASCULINAS": {
        "andrew": "en-US-AndrewNeural",
        "brian": "en-US-BrianNeural",
        "christopher": "en-US-ChristopherNeural",
        "eric": "en-US-EricNeural"
    },
    "FEMENINAS": {
        "emma": "en-US-EmmaNeural",
        "ava": "en-US-AvaNeural",
        "jenny": "en-US-JennyNeural",
        "michelle": "en-US-MichelleNeural"
    }
}

class MicProcessor:
    def __init__(self):
        self.samplerate = 16000
        self.channels = 1
        self.chunk_counter = 0
        self.running = False
        self.translation_queue = None
        self.playback_queue = None
        self.voz = "en-US-AndrewNeural"
        self.is_processing = False

    def load_env(self):
        """Carga variables del archivo .env."""
        env_path = ".env"
        # Buscar .env subiendo niveles
        for _ in range(3):
            if os.path.exists(env_path):
                break
            env_path = "../" + env_path
            
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()

    def translate_audio(self, audio_data) -> str:
        """Llama al endpoint de traducción de Groq (ES➔EN)."""
        self.load_env()
        token = os.environ.get("GROGTOKEN", "")
        if not token:
            print("\033[91m[ERROR]: No se encontró GROGTOKEN en el archivo .env\033[0m")
            return ""

        # Convertir a WAV PCM de 16 bits en memoria
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
                print(f"\033[91m[API ERROR {response.status_code}]: {response.text}\033[0m")
                return ""
        except Exception as e:
            print(f"\033[91m[API EXCEPTION]: {e}\033[0m")
            return ""

    async def synthesize_voice(self, text: str, voice: str, output_file: str):
        """Sintetiza texto en inglés usando edge-tts con reintentos."""
        intentos_maximos = 3
        for intento in range(1, intentos_maximos + 1):
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_file)
                return
            except Exception as e:
                print(f"\033[93m[Advertencia]: Intento {intento}/{intentos_maximos} de Edge-TTS falló ({e}). Reintentando...\033[0m")
                if intento == intentos_maximos:
                    raise e
                await asyncio.sleep(2)

    def iniciar(self, translation_queue: queue.Queue, playback_queue: queue.Queue, voz: str):
        """Inicia el bucle continuo del hilo de traducción."""
        self.translation_queue = translation_queue
        self.playback_queue = playback_queue
        self.voz = voz
        self.running = True
        self.chunk_counter = 0

        while self.running:
            try:
                # Esperar fragmento de audio con un timeout corto para responder al apagado
                audio_data = self.translation_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            self.is_processing = True

            # Traducir con Groq
            english_text = self.translate_audio(audio_data)
            if not english_text:
                self.is_processing = False
                continue

            print(f"\033[96m📝 [TRADUCCIÓN AL INGLÉS]:\033[0m \033[1m{english_text}\033[0m")

            # Asignar nombres únicos de archivos temporales
            mp3_path = f"temp_chunk_{self.chunk_counter}.mp3"
            wav_path = f"temp_chunk_{self.chunk_counter}.wav"
            self.chunk_counter += 1

            # Generar audio con Edge-TTS
            try:
                asyncio.run(self.synthesize_voice(english_text, self.voz, mp3_path))
                # Convertir a WAV con ffmpeg
                os.system(f"ffmpeg -y -i {mp3_path} {wav_path} >/dev/null 2>&1")
                
                # Eliminar MP3 temporal original
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                
                if os.path.exists(wav_path):
                    # Encolar la ruta para el hilo de reproducción
                    self.playback_queue.put(wav_path)
                else:
                    print("\033[91m[ERROR]: Falló conversión WAV de fragmento.\033[0m")
            except Exception as e:
                print(f"\033[91m[ERROR]: Falló síntesis de fragmento: {e}\033[0m")
            finally:
                self.is_processing = False

    def detener(self):
        """Apaga el procesador."""
        self.running = False

# Instancia única exportable
mic_processor = MicProcessor()
