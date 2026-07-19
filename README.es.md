# Traductor & Transcriptor en Tiempo Real (Ubuntu)

> 📖 [Read in English](README.md)

Este proyecto es un procesador de audio en tiempo real diseñado para capturar sonido proveniente de cualquier fuente del sistema (reproductores como VLC, navegadores, videollamadas en Zoom/Teams o micrófonos físicos) en Ubuntu, transcribirlo utilizando la IA Whisper de OpenAI, y opcionalmente traducirlo y sintetizarlo a voz (Text-to-Speech) o imprimirlo de manera estilizada en la consola.

---

## 🎯 Propósito del Proyecto

WhisperBridge nace con la misión de **eliminar las barreras idiomáticas en el ámbito laboral y académico**. Su objetivo principal es permitir a personas asistir a reuniones, webinars o conferencias de trabajo en idiomas que no dominan de forma nativa (como el inglés) y disponer de una traducción o transcripción local y precisa en tiempo real directamente en su terminal o altavoces.

### Filosofía del Proyecto:
*   **Optimización Extrema de Recursos:** Desarrollado bajo la premisa de no saturar el hardware local del usuario. A través de búferes elásticos y colas de control de ejecución, el procesamiento se realiza en lotes eficientes que no interfieren con la fluidez del sistema operativo.
*   **Preparado para el Futuro:** Diseñado de forma modular (POO) de manera que, al dar el salto a APIs externas más potentes, la exactitud lingüística mejore exponencialmente sin requerir cambios de diseño y conservando la ligereza de la aplicación.

---

## 🚀 Arquitectura y Mejoras Realizadas

Hemos llevado a cabo una reestructuración completa del código original enfocado en la estabilidad, rendimiento y buenas prácticas (POO):

1. **Diseño Orientado a Objetos (POO):**
   * **`AudioBridge` (en `bridge.py`):** Clase encargada de capturar los bloques del micrófono y enviarlos a las colas correspondientes, además de manejar el retorno/reproducción local opcional.
   * **`AudioProcessor` (en `processor.py`):** Clase que encapsula el modelo de Inteligencia Artificial (Whisper), el búfer de acumulación de audio y el motor de síntesis de voz (`pyttsx3`).
   * **Exportación de Instancias:** Los archivos exportan directamente las instancias preconfiguradas (`audio_bridge` y `audio_processor`) para simplificar su importación en `main.py`.

2. **Resolución de Conflictos de Audio (Colas de Búfer Elástico):**
   * Separamos el canal de audio en dos colas separadas (`ia_queue` y `playback_queue`).
   * **Aumento de la Cola (`maxsize=500`):** Se incrementó la capacidad de `ia_queue` para almacenar hasta 500 fragmentos de audio (aproximadamente 32 segundos). Esto actúa como un búfer elástico acumulando el trabajo pendiente mientras la IA Whisper realiza inferencia en la CPU. Así, **no se pierde ni una sola palabra o frase** cuando el procesador está ocupado.

3. **Estabilidad en Síntesis de Voz (TTS):**
   * El motor de `pyttsx3` no es seguro para múltiples hilos concurrentes. Se implementó una arquitectura basada en un **hilo de ejecución persistente y exclusivo** (`_worker_voz`) que consume tareas secuenciales de una cola (`voz_queue`), previniendo caídas del programa y fugas de memoria.

4. **Optimización de Latencia y Precisión:**
   * Establecimos el búfer de procesamiento a **80 bloques (~5.12 segundos)**. Esto proporciona a la IA Whisper el contexto de oraciones completas aumentando drásticamente la fidelidad de la transcripción, a la vez que reduce un 60% el consumo de CPU al realizar inferencias con menor frecuencia.

5. **Modos Dinámicos e Inteligencia de Retorno:**
   * Soporta modo **`'escritura'`** (solo imprime en terminal, apaga el motor de voz de fondo y mantiene activo el audio original de fondo para que puedas seguir escuchando el vídeo).
   * Soporta modo **`'voz'`** (lee las traducciones/transcripciones en voz alta y **silencia automáticamente el retorno del audio original** por los altavoces para que escuches únicamente la voz sintetizada de la IA).
   * Tipado estricto con `typing.Literal` para validación estática en el IDE.

6. **Corrección de Advertencias (FP16 / FP32):**
   * Importamos `torch` para comprobar dinámicamente si hay una tarjeta gráfica NVIDIA disponible (`torch.cuda.is_available()`). Si se ejecuta en CPU, deshabilita `fp16` automáticamente (`fp16=False`), eliminando las advertencias molestas en la terminal.

7. **Flexibilidad de Ejecución (Local vs API Cloud):**
   * Se incorporó el parámetro `tipo_uso: TipoUso`.
   * **`'local'`**: Máxima privacidad. Carga Whisper en el hardware local.
   * **`'api'`**: Optimización máxima de hardware. Delega la transcripción a la nube. El archivo `processor.py` incluye el método plantilla `_transcribir_via_api` comentando la conversión a WAV en memoria y cómo estructurar la petición HTTP para que el usuario coloque su clave de API.

---

## 🎛️ Configuración de Audio en Ubuntu (Tubería Virtual)

Para capturar el audio interno del sistema (como un vídeo de YouTube en Firefox o Chrome) y enviarlo al script:

### 1. Crear el Cable Virtual de Audio (Null Sink)
En Ubuntu (utilizando PulseAudio o PipeWire), puedes crear un canal de audio virtual ejecutando en tu terminal:
```bash
pactl load-module module-null-sink sink_name=Virtual_Cable sink_properties=device.description="Virtual_Cable"
```
* Esto creará un dispositivo de salida virtual llamado `Virtual_Cable` y un dispositivo de grabación (monitor) llamado `Virtual_Cable.monitor`.

### 2. Verificar Dispositivos Creados
Para inspeccionar y confirmar los dispositivos activos:
* **Canales de grabación (Entradas):** `pactl list sources short` (buscará `Virtual_Cable.monitor`)
* **Canales de reproducción (Salidas):** `pactl list sinks short` (buscará `Virtual_Cable`)

### 3. Redirección del Audio
1. Abre un reproductor o navegador (ej. YouTube).
2. Ve a la **Configuración de Sonido de Ubuntu** (o usa el comando `pavucontrol` en terminal).
3. En la pestaña de **Reproducción**, cambia la salida de tu navegador de "Altavoces" a **Virtual_Cable**.
4. Ahora, todo el sonido del navegador se irá por esa tubería virtual, la cual será capturada por nuestro script a través de `Virtual_Cable.monitor` (dispositivo de entrada por defecto).

---

## 🛠️ Instalación y Ejecución (Paso a Paso)

Sigue estos pasos para clonar y ejecutar el proyecto desde cero en tu máquina:

### 1. Clonar el Repositorio
```bash
git clone https://github.com/carlosnaico77/WhisperBridge.git
cd WhisperBridge
```

### 2. Instalar Dependencias del Sistema (Linux/Ubuntu)
Dado que la librería `sounddevice` interactúa con el sonido del sistema, requiere que tengas instalado el paquete de desarrollo PortAudio en tu máquina:
```bash
sudo apt update
sudo apt install portaudio19-dev
```

### 3. Configurar el Entorno Virtual de Python
Crea y activa un entorno virtual para mantener las dependencias aisladas de tu sistema operativo:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar Dependencias del Proyecto
Instala las librerías necesarias con un único comando:
```bash
pip install -r requirements.txt
```

### 5. Ejecutar el Proyecto
Inicia el script principal:
```bash
python main.py
```

### 6. Configurar el Modo API (Groq Cloud)
Para obtener transcripciones y traducciones en milisegundos con la máxima precisión (`whisper-large-v3`) sin consumir recursos locales de CPU:
1. Regístrate gratis en **[Groq Console](https://console.groq.com/)** y genera una **API Key**.
2. Crea un archivo llamado `.env` en la raíz del proyecto.
3. Agrega tu API Key dentro del archivo `.env` con la siguiente variable:
   ```env
   GROGTOKEN=tu_api_key_de_groq_aqui
   ```
4. Asegúrate de configurar la variable `tipo_uso` como `'api'` en tu archivo [main.py](file:///home/clozano/Proyectos/TraductorUbuntu/main.py#L16):
   ```python
   tipo_uso: TipoUso = 'api'
   ```
   
> 🔑 **Importante (Restricciones Geográficas / VPN):** Debido a restricciones comerciales, las APIs de Groq y OpenAI bloquean el tráfico de ciertas ubicaciones (como Venezuela), devolviendo un error `Forbidden (403)`. Si este es tu caso, **debes ejecutar una VPN activa a nivel de sistema operativo** (como Proton VPN, que ofrece un plan gratis ilimitado) en tu máquina Ubuntu antes de iniciar el programa.

---

## 🛣️ Trabajo Futuro & Requisitos para Avanzar (Roadmap)

La meta a mediano plazo es habilitar la **traducción automática bidireccional (ej. Inglés ➔ Español)**. Para lograrlo y seguir desarrollando en este entorno, se plantean las siguientes pautas:

### 1. Conectores de APIs en la Nube (Groq / OpenAI)
Para acelerar el procesamiento a milisegundos y usar modelos más potentes (como `Whisper Large-v3`) sin consumir recursos locales de CPU, integraremos llamadas HTTP a las APIs de Groq o OpenAI.

### 🔑 Requisito Crítico: Uso de VPN (Para regiones con bloqueo geográfico como Venezuela)
Debido a regulaciones y restricciones comerciales de empresas estadounidenses, plataformas como OpenAI y Groq restringen el acceso desde ciertas ubicaciones geográficas (retornando error `Forbidden`).
*   **Para desarrollar/probar:** Es obligatorio activar una **VPN activa a nivel de sistema operativo** (como ProtonVPN, Windscribe u otra) en la máquina Ubuntu.
*   **Efecto:** Esto permitirá tanto registrarse y obtener la API Key en las consolas de desarrolladores, como realizar solicitudes HTTP desde el código de Python sin que sean rechazadas por el cortafuegos.

---

## 💻 Entorno de Pruebas (Especificaciones del Autor)

Este proyecto ha sido desarrollado y probado con éxito bajo el siguiente entorno tecnológico:
*   **Sistema Operativo:** Ubuntu Linux (64-bit)
*   **Servidor de Audio:** PipeWire / PulseAudio (usando `module-null-sink`)
*   **Intérprete de Python:** Python 3.14.4 (ejecutado en entorno virtual `venv`)
*   **Compilador del Sistema:** GCC 15.2.0
*   **Hardware de Inferencia:** Ejecución en CPU (con soporte automático para precisión FP32)
*   **Editor/IDE:** VS Code / Cursor (con el intérprete asociado al entorno virtual)

