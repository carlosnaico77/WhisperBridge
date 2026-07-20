# main.py
from services.receptor.initiator import audio_initiator
from services.transmisor.mic_translator import iniciar_traduccion_mic

if __name__ == "__main__":
    # Canal Entrante (Escucha y traduce audio de videollamada al Español)
    # audio_initiator.iniciar(
    #     modo='escritura',
    #     tarea='traducir',
    #     tipo_uso='api'
    # )

    # Canal Saliente (Captura tu micrófono en Español, traduce e inyecta inglés en Virtual_Mic)
    iniciar_traduccion_mic()