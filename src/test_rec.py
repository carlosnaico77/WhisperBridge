# test_rec.py
# pyrefly: ignore [missing-import]
import sounddevice as sd
# pyrefly: ignore [missing-import]
import numpy as np
import time

print("Dispositivos de entrada:")
print(sd.query_devices())

# Buscar dinámicamente el dispositivo
mic_idx = sd.default.device[0]
for idx, d in enumerate(sd.query_devices()):
    if "GeneralPlus" in d['name'] and "monitor" not in d['name'].lower() and d['max_input_channels'] > 0:
        mic_idx = idx
        break

print(f"\nGrabando 3 segundos del micrófono USB (Index {mic_idx})... Habla al micrófono.")
duration = 3.0  # seconds
fs = 16000
myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, device=mic_idx)
sd.wait()  # Esperar a que termine de grabar

amp_max = np.max(np.abs(myrecording))
print(f"\nGrabación terminada.")
print(f"Amplitud máxima detectada: {amp_max:.4f}")

if amp_max == 0:
    print("❌ El micrófono está enviando SILENCIO ABSOLUTO (ceros). Revisa si está silenciado físicamente (botón de mute en el mic) o en la configuración de Ubuntu.")
else:
    print("✅ El micrófono está capturando sonido correctamente!")
