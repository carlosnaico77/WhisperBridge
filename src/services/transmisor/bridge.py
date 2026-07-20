# services/transmisor/bridge.py
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd

class MicBridge:
    def __init__(self):
        self.samplerate = 16000
        self.channels = 1
        self.recording = []
        self.is_recording = False
        self.stream = None

    def find_mic_device(self):
        """Busca el índice del micrófono USB."""
        devices = sd.query_devices()
        for idx, d in enumerate(devices):
            if "GeneralPlus" in d['name'] and d['max_input_channels'] > 0:
                return idx
        return sd.default.device[0]

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback que almacena el audio capturado."""
        if self.is_recording:
            self.recording.append(indata.copy())

    def iniciar_grabacion(self):
        """Inicia la grabación en un flujo de fondo."""
        self.recording = []
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
        """Detiene el flujo de grabación y retorna el audio capturado."""
        if self.stream:
            self.is_recording = False
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        if len(self.recording) > 0:
            return np.concatenate(self.recording, axis=0)
        return np.array([], dtype=np.float32)

# Instancia única exportable
mic_bridge = MicBridge()
