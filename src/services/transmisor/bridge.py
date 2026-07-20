# services/transmisor/bridge.py
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd
import queue

class MicBridge:
    def __init__(self):
        self.samplerate = 16000
        self.channels = 1
        self.block_duration = 0.1  # Bloques de 100ms
        self.block_size = int(self.samplerate * self.block_duration)
        
        # Parámetros VAD por RMS para modo 'streaming'
        self.silence_threshold = 0.015
        self.silence_limit_blocks = 8
        self.min_phrase_samples = int(self.samplerate * 0.5)
        
        self.accumulated_audio = []
        self.silent_block_count = 0
        self.in_speech = False
        
        self.stream = None
        self.translation_queue = None
        self.modo = 'manual'
        self.is_recording = False  # Para modo manual

    def find_mic_device(self):
        """Busca el índice del micrófono USB excluyendo monitores de salida."""
        devices = sd.query_devices()
        for idx, d in enumerate(devices):
            if "GeneralPlus" in d['name'] and "monitor" not in d['name'].lower() and d['max_input_channels'] > 0:
                return idx
        return sd.default.device[0]

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback de sounddevice."""
        if status:
            print(f"[Bridge Status]: {status}")
            
        audio_chunk = indata.copy()
        
        if self.modo == 'streaming':
            # Modo automático por silencios
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            if rms < self.silence_threshold:
                self.silent_block_count += 1
            else:
                self.silent_block_count = 0
                if not self.in_speech:
                    self.in_speech = True
                    
            if self.in_speech:
                self.accumulated_audio.append(audio_chunk)
                if self.silent_block_count >= self.silence_limit_blocks:
                    audio_phrase = np.concatenate(self.accumulated_audio, axis=0)
                    if len(audio_phrase) >= self.min_phrase_samples and self.translation_queue:
                        self.translation_queue.put(audio_phrase)
                    self.accumulated_audio = []
                    self.silent_block_count = 0
                    self.in_speech = False
        else:
            # Modo manual: simplemente acumular si is_recording es True
            if self.is_recording:
                self.accumulated_audio.append(audio_chunk)

    def iniciar(self, translation_queue: queue.Queue, modo: str = 'manual'):
        """Inicia el stream de captura."""
        self.translation_queue = translation_queue
        self.modo = modo
        self.accumulated_audio = []
        self.silent_block_count = 0
        self.in_speech = False
        self.is_recording = False
        
        mic_idx = self.find_mic_device()
        
        # En modo streaming, iniciamos el stream de inmediato
        if self.modo == 'streaming':
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                device=mic_idx,
                callback=self._audio_callback
            )
            self.stream.start()

    def iniciar_grabacion(self):
        """Inicia la grabación manual (usado en modo manual)."""
        if self.modo != 'manual':
            return
        self.accumulated_audio = []
        self.is_recording = True
        mic_idx = self.find_mic_device()
        
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            device=mic_idx,
            callback=self._audio_callback
        )
        self.stream.start()

    def detener_grabacion(self) -> np.ndarray:
        """Detiene la grabación manual y retorna el audio (usado en modo manual)."""
        if self.modo != 'manual':
            return np.array([], dtype=np.float32)
            
        if self.stream:
            self.is_recording = False
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        if len(self.accumulated_audio) > 0:
            return np.concatenate(self.accumulated_audio, axis=0)
        return np.array([], dtype=np.float32)

    def detener(self):
        """Detiene de forma definitiva (principalmente para modo streaming)."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.accumulated_audio = []

# Instancia única exportable
mic_bridge = MicBridge()
