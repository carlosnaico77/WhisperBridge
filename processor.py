# processor.py
import queue
# pyrefly: ignore [missing-import]
import whisper
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pyttsx3
import threading
# pyrefly: ignore [missing-import]
import torch
import urllib.parse
import urllib.request
import json
import io
import wave
import os
# pyrefly: ignore [missing-import]
import requests
from typing import Literal

# Definición de tipos y contratos de interfaz
ModoProcesador = Literal['escritura', 'voz']
TareaProcesador = Literal['transcribir', 'traducir']
TipoUso = Literal['local', 'api']

# Códigos de color ANSI para estilización de la consola
class ColoresConsola:
    VERDE = '\033[92m'
    CIAN = '\033[96m'
    AMARILLO = '\033[93m'
    BLANCO_NEGRITA = '\033[1m'
    GRIS = '\033[90m'
    ROJO = '\033[91m'
    RESET = '\033[0m'

class AudioProcessor:
    def __init__(self):
        self.model = None
        self.buffer = []
        self.buffer_limit = 80
        self.language = 'es'
        
        # Detectamos si CUDA está disponible para usar FP16 localmente
        self.fp16 = torch.cuda.is_available()
        
        self.voz_queue = None
        self.thread_voz = None
        
        # Cargamos las variables de entorno del archivo .env
        self._load_env()

    def _load_env(self):
        """Carga las variables de entorno desde el archivo .env de forma nativa."""
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()

    def _worker_voz(self):
        """Hilo dedicado a la síntesis de voz en segundo plano."""
        engine = pyttsx3.init()
        while True:
            texto = self.voz_queue.get()
            try:
                engine.say(texto)
                engine.runAndWait()
            except Exception as e:
                print(f"{ColoresConsola.ROJO}Error en la síntesis de voz: {e}{ColoresConsola.RESET}")
            self.voz_queue.task_done()

    def _inicializar_voz(self):
        self.voz_queue = queue.Queue()
        self.thread_voz = threading.Thread(target=self._worker_voz, daemon=True)
        self.thread_voz.start()

    def _traducir_texto(self, texto: str, origen: str = 'en', destino: str = 'es') -> str:
        """Traduce texto de inglés a español consumiendo la API libre de MyMemory en memoria."""
        try:
            texto_codificado = urllib.parse.quote(texto)
            url = f"https://api.mymemory.translated.net/get?q={texto_codificado}&langpair={origen}|{destino}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                texto_traducido = data['responseData']['translatedText']
                return texto_traducido
        except Exception as e:
            return f"[Error red traducción: {e}] {texto}"

    def _transcribir_via_api(self, full_audio: np.ndarray) -> str:
        """Transcribe audio en la nube consumiendo la API de Groq."""
        token = os.environ.get("GROGTOKEN", "")
        if not token:
            print(f"{ColoresConsola.ROJO}[ERROR]: No se encontró la variable GROGTOKEN en el archivo .env{ColoresConsola.RESET}")
            return ""

        # 1. Convertir el audio de floats [-1, 1] a enteros PCM de 16 bits en memoria (WAV)
        audio_int16 = (full_audio * 32767).astype(np.int16)
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_int16.tobytes())
        wav_io.seek(0)
        
        # 2. Configurar la llamada HTTP multipart para la API de Groq
        headers = {
            "Authorization": f"Bearer {token}"
        }
        files = {
            "file": ("audio.wav", wav_io, "audio/wav")
        }
        data = {
            "model": "whisper-large-v3",
            "language": self.language
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=12
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "").strip()
            else:
                print(f"{ColoresConsola.ROJO}[API ERROR {response.status_code}]: {response.text}{ColoresConsola.RESET}")
                return ""
        except Exception as e:
            print(f"{ColoresConsola.ROJO}[API EXCEPTION]: {e}{ColoresConsola.RESET}")
            return ""

    def iniciar(self, audio_queue, modo: ModoProcesador = 'escritura', tarea: TareaProcesador = 'transcribir', tipo_uso: TipoUso = 'local'):
        # Configuración de idioma según la tarea
        if tarea == 'traducir':
            self.language = 'en'
        else:
            self.language = 'es'
            
        # Cabecera estilizada de la consola
        print(f"\n{ColoresConsola.CIAN}╔══════════════════════════════════════════════════════════╗{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}║         INICIANDO PROCESADOR DE INTELIGENCIA ARTIFICIAL  ║{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}╚══════════════════════════════════════════════════════════╝{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Entorno de ejecución: {ColoresConsola.BLANCO_NEGRITA}{tipo_uso.upper()}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Modo de salida:       {ColoresConsola.BLANCO_NEGRITA}{modo.upper()}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Tarea activa:         {ColoresConsola.BLANCO_NEGRITA}{tarea.upper()}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Idioma de escucha:    {ColoresConsola.BLANCO_NEGRITA}{self.language.upper()}{ColoresConsola.RESET}")
        if tipo_uso == 'local':
            print(f"{ColoresConsola.VERDE}▶ Aceleración GPU:      {ColoresConsola.BLANCO_NEGRITA}{'ACTIVA (FP16)' if self.fp16 else 'INACTIVA (FP32)'}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}────────────────────────────────────────────────────────────{ColoresConsola.RESET}")
        
        # Si la ejecución es local, cargamos el modelo Whisper de 460MB
        if tipo_uso == 'local':
            print(f"{ColoresConsola.AMARILLO}Cargando modelo local Whisper 'base'...{ColoresConsola.RESET}")
            self.model = whisper.load_model("base")
            
        print(f"{ColoresConsola.AMARILLO}¡Listo! Escuchando audio de la tubería virtual...{ColoresConsola.RESET}\n")
        
        # Solo inicializamos el motor de voz de fondo si el modo es 'voz'
        if modo == 'voz':
            self._inicializar_voz()
        
        while True:
            chunk = audio_queue.get()
            self.buffer.append(chunk)
            
            # Esperamos ~5.12 segundos (80 bloques de ~64ms)
            if len(self.buffer) > self.buffer_limit: 
                full_audio = np.concatenate(self.buffer, axis=0).flatten()
                
                # Procesamos según el tipo de uso seleccionado
                if tipo_uso == 'local':
                    result = self.model.transcribe(full_audio, language=self.language, fp16=self.fp16)
                    texto_obtenido = result['text'].strip()
                else: # tipo_uso == 'api'
                    texto_obtenido = self._transcribir_via_api(full_audio)
                
                if texto_obtenido:
                    if tarea == 'traducir':
                        texto_final = self._traducir_texto(texto_obtenido, origen='en', destino='es')
                        etiqueta = "TRADUCCIÓN (EN➔ES)"
                    else:
                        texto_final = texto_obtenido
                        etiqueta = "TRANSCRIPCIÓN"
                    
                    print(f"{ColoresConsola.VERDE}💻 [{etiqueta}]:{ColoresConsola.RESET} {ColoresConsola.BLANCO_NEGRITA}{texto_final}{ColoresConsola.RESET}")
                    print(f"{ColoresConsola.GRIS}────────────────────────────────────────────────────────────{ColoresConsola.RESET}")
                    
                    # Si el modo es 'voz', enviamos a la cola de TTS
                    if modo == 'voz' and self.voz_queue is not None:
                        self.voz_queue.put(texto_final)
                    
                self.buffer = []

# Exportamos la instancia directamente
audio_processor = AudioProcessor()