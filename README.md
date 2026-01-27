# FFmpeg Video Compressor TUI (Termux) – v3

Compresor de videos para **Android usando Termux**, hecho en **Python + FFmpeg + interfaz de texto (curses)**.

Este programa permite reducir el tamaño de un video ajustando calidad, resolución y audio, ideal para compartir por WhatsApp, Telegram u otras apps.

---

## ¿Qué es este programa?

Es una aplicación que funciona **dentro de la terminal** (no tiene ventanas gráficas) y permite:

✅ Escribir el nombre de un video que esté en el directorio (a mano)
✅ Cambiar resolución
✅ Ajustar calidad (bitrate)
✅ Cambiar audio
✅ Ver el tamaño estimado final
✅ Comprimir el video
✅ Evitar que se sobrescriban archivos
✅ Aprender automáticamente a calcular mejor el tamaño

---

## ¿Qué necesitas antes?

Este programa está pensado para **Android + Termux**.

### 1️⃣ Instalar Termux

Desde F-Droid (recomendado).

### 2️⃣ Instalar dependencias dentro de Termux

Abre Termux y escribe:

```bash
pkg update
pkg upgrade
pkg install python ffmpeg
termux-setup-storage
```

Ese último comando permite acceder a la memoria del teléfono.

---

## Cómo ejecutar el programa

1. Entra a esa carpeta desde Termux.
2. Ejecuta:

```bash
python ffmpegcompressor.py
```

---

## Controles del programa

| Tecla     | Función                                  |
| --------- | ---------------------------------------- |
| ↑ ↓       | Mover entre opciones                     |
| ← →       | Cambiar valor de la opción               |
| **Enter** | Editar archivo o escribir bitrate manual |
| **c**     | Calcular tamaño estimado                 |
| **r**     | Comprimir video                          |
| **s**     | Detener compresión                       |
| **q**     | Salir                                    |

---

## Parámetros que puedes cambiar

### Escala

Cambia la resolución del video:

* Horizontal → formato normal
* Vertical → para videos tipo TikTok / Reels

### Bitrate de video

Controla la calidad del video.
Más alto = mejor calidad = archivo más grande.

### Audio

Puedes cambiar:

* Canales (mono o estéreo)
* Bitrate de audio
* Frecuencia (sample rate)

---

## Bitrate manual (¡función avanzada!)

Puedes escribir cualquier bitrate:

1. Ponte sobre **Bitrate video** o **Bitrate audio**
2. Presiona **Enter**
3. Escribe el número
4. Se guarda para siempre

Estos valores se guardan en:

```
custom_bitrates.json
```

---

## Cálculo de tamaño estimado

El programa calcula cuánto pesará el video antes de comprimir.

Además, aprende con el tiempo usando:

```
correction_factor.json
```

Cada conversión mejora la precisión del cálculo.

---

## Archivos de salida

Nunca se sobrescriben videos.

Ejemplo:

```
video.mp4
video_compressed.mp4
video_compressed_1.mp4
video_compressed_2.mp4
```

---

## Tecnologías usadas

* 🐍 Python
* 🎥 FFmpeg
* 🖥 curses (interfaz de texto)
* 📱 Termux (Linux en Android)

---

## ¿Para qué sirve aprender con este proyecto?

Este programa enseña:

✔ Manejo de archivos
✔ Uso de procesos externos (FFmpeg)
✔ Interfaces de texto
✔ Cálculo de tamaños digitales
✔ Automatización
✔ Persistencia con JSON

Es un excelente ejemplo de proyecto práctico de informática.

---

## Consejo

Si quieres explorar los archivos de tu teléfono usa rutas como:

```
/storage/emulated/0/Download/video.mp4
```

---

## Autor

Proyecto educativo para compresión de video en Android usando herramientas libres.

- Washington Indacochea Delgado

---
