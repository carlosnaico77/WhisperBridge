# main.py
from services.receptor.initiator import audio_initiator
from services.transmisor.mic_translator import iniciar_traduccion_mic, VOCES_DISPONIBLES, probar_voces_masculinas

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
    
    voz_seleccionada = VOCES_DISPONIBLES['MASCULINAS']['brian']

    # 1. Bucle de Audición Temporal de Voces Masculinas
    probar_voces_masculinas()

    # 2. Canal Saliente (Desactiva el de arriba y activa este al terminar las pruebas)
    # iniciar_traduccion_mic(escuchar_retorno=True, voz=voz_seleccionada)