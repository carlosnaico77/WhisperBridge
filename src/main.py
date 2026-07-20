# main.py
import threading
import queue
from services.bridge import audio_bridge
from services.processor import audio_processor, ModoProcesador, TareaProcesador, TipoUso

if __name__ == "__main__":
    # Aumentamos el tamaño máximo para acumular audio y evitar pérdidas mientras la IA procesa
    ia_queue = queue.Queue(maxsize=500)
    playback_queue = queue.Queue(maxsize=100)
    
    # Configuración de ejecución:
    # ▶ modo:     'escritura' (solo consola) o 'voz' (lectura hablada de la transcripción/traducción)
    # ▶ tarea:    'transcribir' (audio español ➔ texto español) o 'traducir' (audio inglés ➔ traducción español)
    # ▶ tipo_uso: 'local' (100% privado offline en CPU) o 'api' (procesamiento en la nube usando tokens)
    modo: ModoProcesador = 'escritura'
    tarea: TareaProcesador = 'traducir'
    tipo_uso: TipoUso = 'api'
    
    # Arrancamos el procesador de IA en un hilo separado indicando el modo, la tarea y el tipo de uso
    ia_thread = threading.Thread(target=audio_processor.iniciar, args=(ia_queue, modo, tarea, tipo_uso), daemon=True)
    ia_thread.start()
    
    # Si el modo de la IA es 'voz', muteamos el retorno del audio original
    # para escuchar únicamente la traducción sintetizada.
    mute_retorno = (modo == 'voz')
    
    # Arrancamos el puente de audio en el hilo principal
    try:
        audio_bridge.iniciar(playback_queue, ia_queue, mute_playback=mute_retorno)
    except KeyboardInterrupt:
        print("\nApagando sistema...")