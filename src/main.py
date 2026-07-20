# main.py
from services.receptor.initiator import audio_initiator

if __name__ == "__main__":
    # Configuración de ejecución:
    # ▶ modo:     'escritura' (solo consola) o 'voz' (lectura hablada de la transcripción/traducción)
    # ▶ tarea:    'transcribir' (audio español ➔ texto español) o 'traducir' (audio inglés ➔ traducción español)
    # ▶ tipo_uso: 'local' (100% privado offline en CPU) o 'api' (procesamiento en la nube usando tokens)
    audio_initiator.iniciar(
        modo='escritura',
        tarea='traducir',
        tipo_uso='api'
    )