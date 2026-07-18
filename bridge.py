# bridge.py
# pyrefly: ignore [missing-import]
import sounddevice as sd
import queue

class AudioBridge:
    def __init__(self):
        self.input_id = None
        self.output_id = None
        self.block_size = 1024
        self.playback_queue = None
        self.ia_queue = None
        self.mute_playback = False

    def _input_callback(self, indata, frames, time, status):
        # Enviamos una copia a la IA siempre
        if self.ia_queue is not None:
            try:
                self.ia_queue.put_nowait(indata.copy())
            except queue.Full:
                pass
        
        # Enviamos copia para la reproducción/retorno local SOLO si no está muteado
        if not self.mute_playback and self.playback_queue is not None:
            try:
                self.playback_queue.put_nowait(indata.copy())
            except queue.Full:
                pass

    def _output_callback(self, outdata, frames, time, status):
        # Solo reproducimos sonido original si no está muteado
        if not self.mute_playback and self.playback_queue is not None:
            try:
                # Intentamos sacar de la cola de reproducción
                data = self.playback_queue.get_nowait()
                outdata[:len(data), :] = data
            except queue.Empty:
                outdata.fill(0)
        else:
            outdata.fill(0)

    def iniciar(self, playback_queue, ia_queue, mute_playback=False):
        self.playback_queue = playback_queue
        self.ia_queue = ia_queue
        self.mute_playback = mute_playback
        
        estado_retorno = "Muteado" if self.mute_playback else "Activo"
        
        with sd.InputStream(device=self.input_id, channels=1, callback=self._input_callback, samplerate=16000, blocksize=self.block_size), \
             sd.OutputStream(device=self.output_id, channels=1, callback=self._output_callback, samplerate=16000, blocksize=self.block_size):
            print(f"Puente activo. IA escuchando... (Retorno original: {estado_retorno})")
            while True:
                sd.sleep(1000)

# Exportamos la instancia directamente
audio_bridge = AudioBridge()