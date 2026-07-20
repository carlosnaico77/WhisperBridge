# main.py
from services.receptor.initiator import audio_initiator
from services.transmisor.initiator import transmitter_initiator, VOCES_DISPONIBLES

if __name__ == "__main__":
    # Canal Entrante (Escucha y traduce audio de videollamada al Español)
    # audio_initiator.iniciar(
    #     modo='escritura',
    #     tarea='traducir',
    #     tipo_uso='api'
    # )

    # Voces US recomendadas:
    # ▶ Masculinas: VOCES_DISPONIBLES['MASCULINAS']['andrew'] (por defecto) o ['brian'], ['christopher'], ['eric']
    # ▶ Femeninas:  VOCES_DISPONIBLES['FEMENINAS']['emma'] o ['ava'], ['jenny'], ['michelle']
    
    voz_seleccionada = VOCES_DISPONIBLES['MASCULINAS']['andrew']

    # Canal Saliente (Captura tu micrófono en Español, traduce e inyecta inglés en Virtual_Mic)
    transmitter_initiator.iniciar(escuchar_retorno=True, voz=voz_seleccionada)