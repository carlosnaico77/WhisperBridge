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
from typing import Literal

# Definición del tipo permitido para el modo de ejecución (Interfaz/Tipo de unión)
ModoProcesador = Literal['escritura', 'voz']

class AudioProcessor:
    def __init__(self):
        self.model_name = 'base' # Opciones: 'tiny', 'base', 'small', 'medium', 'large'
        self.model = None
        self.buffer = []
        self.buffer_limit = 80
        self.language = 'es'
        
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
                print(f"Error en la síntesis de voz: {e}")
            self.voz_queue.task_done()

    def _inicializar_voz(self):
        self.voz_queue = queue.Queue()
        self.thread_voz = threading.Thread(target=self._worker_voz, daemon=True)
        self.thread_voz.start()

    def iniciar(self, audio_queue, modo: ModoProcesador = 'escritura'):
        print(f"Motor de IA cargado en modo '{modo}'. Esperando audio...")
        self.model = whisper.load_model("base")
        
        # Solo inicializamos el motor de voz de fondo si el modo es 'voz'
        if modo == 'voz':
            self._inicializar_voz()
        
        while True:
            chunk = audio_queue.get()
            self.buffer.append(chunk)
            
            # Esperamos ~5.12 segundos (80 bloques de ~64ms) para mayor precisión y menor uso de CPU
            if len(self.buffer) > self.buffer_limit: 
                full_audio = np.concatenate(self.buffer, axis=0).flatten()
                
                # Transcribimos directamente en el idioma configurado
                result = self.model.transcribe(full_audio, language=self.language, fp16=self.fp16)
                texto_transcrito = result['text'].strip()
                
                if texto_transcrito:
                    print(f"\n[TRANSCRIPCIÓN]: {texto_transcrito}")
                    
                    # Si el modo es 'voz', enviamos a la cola de TTS
                    if modo == 'voz' and self.voz_queue is not None:
                        self.voz_queue.put(texto_transcrito)
                    
                self.buffer = []

# Exportamos la instancia directamente
audio_processor = AudioProcessor()