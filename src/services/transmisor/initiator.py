# services/transmisor/initiator.py
import threading
import queue
import time
from services.transmisor.bridge import mic_bridge
from services.transmisor.processor import mic_processor
from services.transmisor.player import mic_player
from services.transmisor.processor import TipoVoz, VOCES_DISPONIBLES

# Códigos de color ANSI para la terminal
class ColoresConsola:
    VERDE = '\033[92m'
    CIAN = '\033[96m'
    AMARILLO = '\033[93m'
    BLANCO_NEGRITA = '\033[1m'
    GRIS = '\033[90m'
    ROJO = '\033[91m'
    RESET = '\033[0m'

class TransmitterInitiator:
    def __init__(self):
        self.translation_queue = None
        self.playback_queue = None
        self.processor_thread = None
        self.player_thread = None
        self.running = False

    def iniciar(self, escuchar_retorno: bool = False, voz: TipoVoz = "en-US-AndrewNeural"):
        """Orquesta e inicia las colas y los hilos para el canal saliente."""
        print(f"\n{ColoresConsola.CIAN}╔══════════════════════════════════════════════════════════╗{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}║         INICIANDO TRADUCTOR DE MICRÓFONO (MANUAL)        ║{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}╚══════════════════════════════════════════════════════════╝{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Voz seleccionada:       {ColoresConsola.BLANCO_NEGRITA}{voz}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.VERDE}▶ Retorno en auriculares: {ColoresConsola.BLANCO_NEGRITA}{'ACTIVO' if escuchar_retorno else 'DESACTIVADO'}{ColoresConsola.RESET}")
        print(f"{ColoresConsola.CIAN}────────────────────────────────────────────────────────────{ColoresConsola.RESET}\n")

        self.translation_queue = queue.Queue(maxsize=100)
        self.playback_queue = queue.Queue(maxsize=50)
        self.running = True

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

        # 3. Control manual interactivo mediante ENTER en el hilo principal
        try:
            while self.running:
                input(f"{ColoresConsola.AMARILLO}👉 Presiona ENTER para empezar a hablar (Habla en Español)...{ColoresConsola.RESET}")
                mic_bridge.iniciar_grabacion()
                
                input(f"{ColoresConsola.VERDE}🎤 Grabando... Presiona ENTER para detener y procesar...{ColoresConsola.RESET}")
                audio_data = mic_bridge.detener_grabacion()
                
                if len(audio_data) == 0:
                    print(f"{ColoresConsola.ROJO}No se capturó audio.{ColoresConsola.RESET}\n")
                    continue
                
                # Calcular amplitud máxima para depurar si entra sonido
                amp_max = np.max(np.abs(audio_data))
                print(f"{ColoresConsola.GRIS}[DEBUG] Fragmento: {len(audio_data)} muestras, Amplitud Max: {amp_max:.4f}{ColoresConsola.RESET}")
                
                # Ignorar si es puro silencio absoluto
                if amp_max < 0.005:
                    print(f"{ColoresConsola.ROJO}Audio descartado por ser demasiado silencioso.{ColoresConsola.RESET}\n")
                    continue
                
                # Encolamos el audio capturado para procesamiento en segundo plano
                self.translation_queue.put(audio_data)
                
        except KeyboardInterrupt:
            print(f"\n{ColoresConsola.AMARILLO}Apagando traductor de micrófono...{ColoresConsola.RESET}")
        finally:
            self.detener()

    def detener(self):
        """Detiene de forma segura todos los streams e hilos."""
        self.running = False
        mic_bridge.detener_grabacion()
        mic_processor.detener()
        mic_player.detener()
        
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=1.5)
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join(timeout=1.5)
        print(f"{ColoresConsola.VERDE}Sistema apagado correctamente.{ColoresConsola.RESET}")

# Instancia única exportable
transmitter_initiator = TransmitterInitiator()
