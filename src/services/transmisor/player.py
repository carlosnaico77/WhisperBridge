# services/transmisor/player.py
import os
import queue
import time

class MicPlayer:
    def __init__(self):
        self.running = False
        self.playback_queue = None
        self.escuchar_retorno = False

    def iniciar(self, playback_queue: queue.Queue, escuchar_retorno: bool):
        """Inicia el bucle continuo del hilo de reproducción secuencial."""
        self.playback_queue = playback_queue
        self.escuchar_retorno = escuchar_retorno
        self.running = True

        while self.running:
            try:
                # Esperar archivo WAV con un timeout corto
                wav_path = self.playback_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if os.path.exists(wav_path):
                print(f"\033[92m🔊 Inyectando fragmento traducido en Virtual_Mic...\033[0m")
                
                if self.escuchar_retorno:
                    # Reproducir en Virtual_Mic en segundo plano
                    os.system(f"paplay --device=Virtual_Mic {wav_path} &")
                    # Reproducir en auriculares en primer plano (bloqueante)
                    os.system(f"paplay {wav_path}")
                else:
                    # Reproducir únicamente en Virtual_Mic de forma bloqueante
                    os.system(f"paplay --device=Virtual_Mic {wav_path}")
                
                # Eliminar archivo WAV temporal de forma segura
                try:
                    os.remove(wav_path)
                except Exception as e:
                    print(f"[Advertencia]: No se pudo borrar {wav_path} ({e})")
            
            self.playback_queue.task_done()

    def detener(self):
        """Apaga el reproductor."""
        self.running = False

# Instancia única exportable
mic_player = MicPlayer()
