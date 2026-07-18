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
from typing import Literal

# Definición de tipos y contratos de interfaz
ModoProcesador = Literal['escritura', 'voz']
TareaProcesador = Literal['transcribir', 'traducir']

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
        self.language = 'es' # Idioma por defecto para transcribir
        
        # Detectamos si CUDA (GPU) está disponible para usar FP16, de lo contrario usamos FP32 (CPU)
        self.fp16 = torch.cuda.is_available()
        
        self.voz_queue = None
        self.thread_voz = None

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
            # En caso de fallo o timeout de red, devolvemos el texto original para no interrumpir el programa
            return f"[Error red traducción: {e}] {texto}"

    def iniciar(self, audio_queue, modo: ModoProcesador = 'escritura', tarea: TareaProcesador = 'transcribir'):
        # Configuración del idioma de Whisper según la tarea
        if tarea == 'traducir':
            self.language = 'en' # Para traducir inglés-español, Whisper debe escuchar en inglés
        else:
            self.language = 'es' # Para transcripción normal en español
            
        # Dibujamos una cabecera estilizada en la consola
        print(f"\n{ColoresConsola.CIAN}╔══════════════════════════════════════════════════════════╗{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}║         INICIANDO PROCESADOR DE INTELIGENCIA ARTIFICIAL  ║{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}╚══════════════════════════════════════════════════════════╝{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Modo de salida:     {ColoresConsola.BLANCO_NEGRITA}{modo.upper()}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Tarea activa:       {ColoresConsola.BLANCO_NEGRITA}{tarea.upper()}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Idioma de escucha:  {ColoresConsola.BLANCO_NEGRITA}{self.language.upper()}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Aceleración GPU:    {ColoresConsola.BLANCO_NEGRITA}{'ACTIVA (FP16)' if self.fp16 else 'INACTIVA (FP32)'}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}────────────────────────────────────────────────────────────{ColoresConsola.RESET}")
        
        # Cargamos el modelo Whisper base
        self.model = whisper.load_model("base")
        print(f"{ColoresConsola.AMARILLO}¡Listo! Escuchando audio de la tubería virtual...{ColoresConsola.RESET}\n")
        
        # Solo inicializamos el motor de voz de fondo si el modo es 'voz'
        if modo == 'voz':
            self._inicializar_voz()
        
        while True:
            chunk = audio_queue.get()
            self.buffer.append(chunk)
            
            # Esperamos ~5.12 segundos (80 bloques de ~64ms) para mayor precisión
            if len(self.buffer) > self.buffer_limit: 
                full_audio = np.concatenate(self.buffer, axis=0).flatten()
                
                # Ejecutamos la transcripción inicial con Whisper
                result = self.model.transcribe(full_audio, language=self.language, fp16=self.fp16)
                texto_obtenido = result['text'].strip()
                
                if texto_obtenido:
                    if tarea == 'traducir':
                        # Traducimos de inglés a español
                        texto_final = self._traducir_texto(texto_obtenido, origen='en', destino='es')
                        etiqueta = "TRADUCCIÓN (EN➔ES)"
                    else:
                        texto_final = texto_obtenido
                        etiqueta = "TRANSCRIPCIÓN"
                    
                    # Imprimimos de manera elegante en la terminal
                    print(f"{ColoresConsola.VERDE}💻 [{etiqueta}]:{ColoresConsola.RESET} {ColoresConsola.BLANCO_NEGRITA}{texto_final}{ColoresConsola.RESET}")
                    print(f"{ColoresConsola.GRIS}────────────────────────────────────────────────────────────{ColoresConsola.RESET}")
                    
                    # Si el modo es 'voz', enviamos a la cola de TTS
                    if modo == 'voz' and self.voz_queue is not None:
                        self.voz_queue.put(texto_final)
                    
                self.buffer = []

# Exportamos la instancia directamente
audio_processor = AudioProcessor()