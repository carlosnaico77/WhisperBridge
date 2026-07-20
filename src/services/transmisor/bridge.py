# services/transmisor/bridge.py
import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd
import queue
import time

class MicBridge:
    def __init__(self):
        self.samplerate = 16000
        self.channels = 1
        self.block_duration = 0.1  # Bloques de 100ms
        self.block_size = int(self.samplerate * self.block_duration)
        
        # Parámetros del detector de silencio (VAD simple por RMS)
        self.silence_threshold = 0.015  # Umbral de volumen (RMS)
        self.silence_limit_blocks = 8   # 8 bloques seguidos de 100ms = 0.8s de silencio
        self.min_phrase_samples = int(self.samplerate * 0.5)  # Ignorar ruidos menores a 0.5s
        
        self.accumulated_audio = []
        self.silent_block_count = 0
        self.in_speech = False
        
        self.stream = None
        self.translation_queue = None

    def find_mic_device(self):
        """Busca el índice del micrófono USB."""
        devices = sd.query_devices()
        for idx, d in enumerate(devices):
            if "GeneralPlus" in d['name'] and d['max_input_channels'] > 0:
                return idx
        # Fallback al por defecto
        return sd.default.device[0]

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback de sounddevice que procesa bloques de audio en tiempo real."""
        if status:
            print(f"[Bridge Status]: {status}")
            
        # Calcular el volumen RMS del bloque actual
        audio_chunk = indata.copy()
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        if rms < self.silence_threshold:
            self.silent_block_count += 1
        else:
            self.silent_block_count = 0
            if not self.in_speech:
                self.in_speech = True
                
        if self.in_speech:
            self.accumulated_audio.append(audio_chunk)
            
            # Si detectamos suficiente silencio continuo, cortamos la frase
            if self.silent_block_count >= self.silence_limit_blocks:
                audio_phrase = np.concatenate(self.accumulated_audio, axis=0)
                
                # Solo encolar si el fragmento tiene una duración mínima razonable
                if len(audio_phrase) >= self.min_phrase_samples:
                    if self.translation_queue:
                        self.translation_queue.put(audio_phrase)
                
                # Reiniciar estado para la siguiente frase
                self.accumulated_audio = []
                self.silent_block_count = 0
                self.in_speech = False

    def iniciar(self, translation_queue: queue.Queue):
        """Arranca el stream continuo de captura de audio."""
        self.translation_queue = translation_queue
        self.accumulated_audio = []
        self.silent_block_count = 0
        self.in_speech = False
        
        mic_idx = self.find_mic_device()
        
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            blocksize=self.block_size,
            device=mic_idx,
            callback=self._audio_callback
        )
        self.stream.start()

    def detener(self):
        """Apaga el stream de captura."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        # Si quedó audio acumulado al apagar, procesarlo
        if len(self.accumulated_audio) > 0:
            audio_phrase = np.concatenate(self.accumulated_audio, axis=0)
            if len(audio_phrase) >= self.min_phrase_samples and self.translation_queue:
                self.translation_queue.put(audio_phrase)
        self.accumulated_audio = []

# Instancia única exportable
mic_bridge = MicBridge()
