# services/transmisor/initiator.py
import threading
import queue
import time
from services.transmisor.bridge import mic_bridge
from services.transmisor.processor import mic_processor
from services.transmisor.player import mic_player, MicPlayer
from services.transmisor.bridge import MicBridge
from services.transmisor.processor import MicProcessor

# Traemos el tipo de voces e importamos el catálogo para exportación
from services.transmisor.processor import TipoVoz, VOCES_DISPONIBLES

class TransmitterInitiator:
    def __init__(self):
        self.translation_queue = None
        self.playback_queue = None
        self.processor_thread = None
        self.player_thread = None

    def iniciar(self, escuchar_retorno: bool = False, voz: TipoVoz = "en-US-AndrewNeural"):
        """Orquesta e inicia las colas y los hilos para el canal saliente."""
        print(f"\n\033[96m╔══════════════════════════════════════════════════════════╗\033[0m")
        print(f"\033[96m║         INICIANDO TRADUCTOR DE MICRÓFONO (STREAMING)     ║\033[0m")
        print(f"\033[96m╚══════════════════════════════════════════════════════════╝\033[0m")
        print(f"\033[92m▶ Voz seleccionada:       \033[1m{voz}\033[0m")
        print(f"\033[92m▶ Retorno en auriculares: \033[1m{'ACTIVO' if escuchar_retorno else 'DESACTIVADO'}\033[0m")
        print(f"\033[96m────────────────────────────────────────────────────────────\033[0m\n")

        self.translation_queue = queue.Queue(maxsize=100)
        self.playback_queue = queue.Queue(maxsize=50)

        # 1. Iniciar hilo del Procesador (IA + TTS)
        self.processor_thread = threading.Thread(
            target=mic_processor.iniciar,
            args=(self.translation_queue, self.playback_queue, voz),
            daemon=True
        )
        self.processor_thread.start()

        # 2. Iniciar hilo del Reproductor Secuencial
        self.player_thread = threading.Thread(
            target=mic_player.iniciar,
            args=(self.playback_queue, escuchar_retorno),
            daemon=True
        )
        self.player_thread.start()

        # 3. Iniciar el puente de audio del micrófono (hilo principal)
        print("\033[93m¡Listo! Escuchando micrófono de forma continua...\033[0m")
        print("\033[90mHabla libremente con pausas naturales. Presiona CTRL+C para salir.\033[0m\n")
        
        try:
            mic_bridge.iniciar(self.translation_queue)
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\033[93mApagando traductor de micrófono...\033[0m")
        finally:
            self.detener()

    def detener(self):
        """Detiene de forma segura todos los streams e hilos."""
        mic_bridge.detener()
        mic_processor.detener()
        mic_player.detener()
        
        # Esperar a que los hilos terminen si es posible
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=2.0)
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join(timeout=2.0)
        print("\033[92mSistema apagado correctamente.\033[0m")

# Instancia única exportable
transmitter_initiator = TransmitterInitiator()
