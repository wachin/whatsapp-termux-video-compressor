# FFmpeg Video Compressor TUI (Termux) - v3

Compresor de videos para **Android usando Termux**, hecho en **Python + FFmpeg + interfaz de texto (curses)**, pero también funciona en una terminal Linux.

Este programa permite reducir el tamaño de un video ajustando calidad, resolución y audio, ideal para compartir por WhatsApp, Telegram u otras apps. Al iniciar permite elegir idioma: **English** por defecto o **Español**.

# Caso de uso

Yo tenía un video de 900 MB en mi celular que quería subir a WhatsApp, pero WhatsApp mostró un mensaje diciendo que lo iba a recortar hasta dejarlo en 180 MB. El video duraba 10 minutos y, si lo recortaba, iba a quedar más corto. Con este programa lo reduje a menos de 180 MB observando el tamaño final estimado mientras ajustaba los parámetros. Después de comprimirlo, pude enviarlo completo y WhatsApp no me pidió recortarlo.

---

## ¿Qué es este programa?

Es una aplicación que funciona **dentro de la terminal**. No usa una ventana gráfica. Permite:

- Elegir el idioma al iniciar: inglés o español
- Buscar videos con un selector de archivos dentro de Termux
- Cambiar la resolución del video
- Ajustar la calidad de video y audio mediante bitrates
- Ver el tamaño final estimado aproximado
- Abrir una ayuda integrada de Termux
- Comprimir el video

---

## Requisitos

Este programa está pensado para **Android + Termux**, pero también funciona en Linux.

### 1. Instalar Termux

Instala Termux desde F-Droid.

**Nota:** algunos celulares Xiaomi también pueden incluir una versión actualizada y completa de Termux.

No uses la versión de Termux que viene en Play Store porque no es una versión completa.

### 2. Instalar dependencias dentro de Termux

Abre Termux y ejecuta:

```bash
pkg update
pkg upgrade
pkg install git python ffmpeg
```

Luego ejecuta:

```bash
termux-setup-storage
```

Ese último comando permite que Termux acceda al almacenamiento del teléfono.

---

## Acceder al almacenamiento interno

Para permitir que Termux acceda al almacenamiento interno, ejecuta:

```bash
termux-setup-storage
```

Presiona Enter y acepta el permiso de Android.

Para clonar un repositorio dentro del almacenamiento interno, primero debes llegar allí. En Termux ejecuta:

```bash
cd storage
```

Luego ejecuta:

```bash
ls
```

para ver las carpetas disponibles.

Después entra al almacenamiento compartido:

```bash
cd shared
```

Atajo: puedes hacer lo mismo con:

```bash
cd /sdcard
```

Cualquiera de los dos métodos te lleva al almacenamiento interno compartido.

Para saber en qué ruta estás ubicado en Termux, ejecuta:

```bash
pwd
```

y presiona Enter.

**Nota:** cuando abres Termux por primera vez, empiezas en la carpeta home de Termux:

```text
/data/data/com.termux/files/home
```

Si ya estás en el almacenamiento interno usando `cd shared`, el prompt puede verse así:

```text
~/storage/shared $
```

Si usaste `cd /sdcard`, puede verse así:

```text
/sdcard $
```

> **Nota:** es importante saber dónde estás ubicado. Si por accidente clonaste un repositorio dentro de la carpeta home de Termux o dentro de `storage`, puedes moverlo con `mv`. Si estás en `/data/data/com.termux/files/home` y clonaste un repo llamado `mirepo`, primero muévelo a `storage` con `mv mirepo storage`, luego muévelo al almacenamiento interno compartido con `mv mirepo shared`. Si lo clonaste directamente dentro de `storage`, usa `mv mirepo shared`. Si estás en `shared` y quieres volver a la carpeta home de Termux, ejecuta `cd`.

## Cómo ejecutar el programa

1. Clona o descarga este repositorio dentro del almacenamiento interno al que llegas gracias a `/sdcard`.
2. Entra a la carpeta del repositorio desde Termux con `cd` seguido del nombre del repositorio.
3. Ejecuta:

```bash
python ffmpegcompressor.py
```

Al abrir, primero aparece el selector de idioma. **English** aparece seleccionado por defecto; usa las flechas para elegir **Español** si lo prefieres y presiona **Enter**.

## Captura de pantalla

![Interfaz del compresor en Termux](images/20260621_141116_Termux.jpg)

## Ayuda integrada

En el menú principal, baja con las flechas hasta:

```text
Ayuda Termux integrada | Enter ver
```

Presiona **Enter** para abrir la ayuda integrada dentro de la terminal. Allí se explica:

- Teclas principales del compresor
- Por qué se eligieron los valores de compresión por defecto
- Valores disponibles y ejemplos antiguos de compresión para WhatsApp
- Archivos locales de configuración

Usa **Arriba/Abajo** para desplazarte. Para volver al menú principal, presiona **q**, **ESC** o **Enter**.

![Ayuda Termux](images/20260621_171214_Help_Termux.jpg)

---

## Controles del programa

| Tecla | Función |
| ----- | ------- |
| Arriba / Abajo | Moverse entre opciones |
| Izquierda / Derecha | Bajar/subir el valor marcado |
| **Enter** | Elegir/editar la opción marcada |
| **c** | Recalcular tamaño estimado |
| **f** | Buscar video con el selector de archivos |
| **r** | Comprimir video / iniciar proceso |
| **s** | Detener mientras está comprimiendo |
| **q** | Salir |

---

## Cómo cargar un video

Después de elegir el idioma, aparece el selector de archivos.

Puedes navegar con las flechas:

- **Arriba / Abajo**: moverse por carpetas y videos
- **Enter**: abrir una carpeta o elegir un video
- **q** o **ESC**: cancelar

Una forma simple de usarlo es colocar el video dentro de la carpeta del repositorio:

```text
whatsapp-termux-video-compressor
```

Luego abre el programa y elige el video desde el selector de archivos.

Después de elegir el video, presiona **c** para recalcular el tamaño estimado si cambias parámetros, **r** para iniciar la compresión y **s** para detenerla mientras está comprimiendo.

---

## Parámetros que puedes cambiar

En los valores numéricos, **Izquierda** disminuye y **Derecha** aumenta. Esto aplica a bitrate de video, framerate, canales de audio, bitrate de audio y frecuencia de audio.

### Escala

Cambia la resolución del video:

- Horizontal / Landscape: formato normal
- Vertical / Portrait: para videos tipo TikTok / Reels

En **Escala**, las flechas izquierda/derecha alternan entre las opciones disponibles.

Cuando **Scale / Escala** está marcado, puedes cambiar entre `scale=512:288` y `scale=288:512` con **Izquierda / Derecha** o presionando **Enter**.

### Bitrate de video

Controla la calidad del video.
Valor más alto = mejor calidad = archivo más grande.

### Audio

Puedes cambiar:

- Canales: mono o estéreo
- Bitrate de audio
- Frecuencia de audio

---

## Por qué estos valores por defecto

El programa inicia con estos valores:

| Parámetro | Valor por defecto | Motivo práctico |
| --------- | ----------------- | --------------- |
| Escala | `scale=512:288` | Reduce la resolución para bajar mucho el tamaño del video. |
| Bitrate video | `200k` | Mantiene una calidad aceptable en pantalla de teléfono sin hacer el archivo demasiado grande. |
| Framerate | `15` | Reduce los cuadros por segundo y baja el tamaño final. |
| Canales audio | `1` | Usa audio mono; para voz o videos casuales suele ser suficiente y pesa menos que estéreo. |
| Bitrate audio | `64k` | Da más calidad de audio que las pruebas antiguas de 18k-30k sin dejar de ser liviano. |
| Frecuencia audio | `44100 Hz` | Frecuencia de audio común y compatible. |

Estos valores vienen de pruebas manuales antiguas con FFmpeg/FFmulticonverter [hechas por mí](https://gist.github.com/wachin/643b01ece5724ceba23d3408db53db28) para enviar videos por WhatsApp cuando el límite era mucho menor, alrededor de **16 MB**. Esas pruebas usaban comandos como:

```bash
-vf "scale=512:288" -b:v 200k -r 15 -ac 1 -b:a 30k -ar 44100
```

La idea era siempre la misma:

- Reducir la resolución con `scale=512:288`.
- Bajar el bitrate de video para controlar el tamaño.
- Usar `15 fps` para reducir cuadros por segundo.
- Convertir el audio a mono con `-ac 1`.
- Usar un bitrate de audio bajo.
- Mantener `44100 Hz` por compatibilidad.

Hoy WhatsApp permite enviar videos de mayor tamaño, por eso este programa usa valores un poco más cómodos, especialmente en audio (`64k` en vez de 18k-30k). Aun así, los valores por defecto siguen siendo un buen punto de partida porque comprimen bastante sin obligarte a calcular todo desde cero.

Si el video todavía queda muy grande, baja primero el **bitrate de video**. Si aún necesitas reducir más, prueba bajar el **bitrate de audio** o usar un valor de video más bajo. Después presiona **c** para recalcular el tamaño estimado.

---

## Bitrate manual (avanzado)

Puedes escribir cualquier bitrate:

1. Muévete hasta **Bitrate video** o **Bitrate audio**.
2. Presiona **Enter**.
3. Escribe el número.
4. Se guarda de forma permanente.

Estos valores se guardan en:

```text
custom_bitrates.json
```

---

## ¿Cuántos formatos de video acepta?

El programa realmente no limita formatos.
**FFmpeg** se encarga de eso.

FFmpeg soporta casi todos los formatos comunes de video.

### Formatos comunes que FFmpeg suele soportar

| Tipo | Formatos comunes |
| ---- | ---------------- |
| Móvil | MP4, 3GP, MOV |
| PC | AVI, MKV, WMV |
| Internet | WEBM, FLV |
| TV/HD | MPEG, MPG, TS, MTS, M2TS |
| Cámaras | MOV, MTS, MXF |

---

### ¿Por qué tantos?

Porque el programa simplemente ejecuta:

```bash
ffmpeg -i archivo
```

y FFmpeg detecta el formato automáticamente.

---

## Cálculo de tamaño estimado

El programa estima cuánto pesará el video antes de comprimir.

También aprende con el tiempo usando:

```text
correction_factor.json
```

Cada conversión mejora la precisión de la estimación.

Formato:

```json
{
  "factor": 1.08,
  "n": 0
}
```

- `factor`: multiplicador usado para ajustar la estimación.
- `n`: cantidad de conversiones usadas para calcular ese factor.

Este archivo no se sube a GitHub porque es generado por el programa y depende de las conversiones hechas en cada teléfono.

---

## Archivos locales ignorados

Estos archivos se guardan localmente, pero están excluidos en `.gitignore`:

```text
correction_factor.json
custom_bitrates.json
```

Ambos contienen datos generados o preferencias personales del usuario:

- `correction_factor.json`: cambia después de comprimir videos y ajusta las estimaciones según resultados reales.
- `custom_bitrates.json`: guarda bitrates manuales agregados por el usuario.

Para documentar el formato sin subir datos locales, el repositorio incluye:

```text
correction_factor.example.json
custom_bitrates.example.json
```

Formato de `custom_bitrates.json`:

```json
{
  "video": [275],
  "audio": [72]
}
```

- `video`: lista de bitrates de video personalizados en kbit/s.
- `audio`: lista de bitrates de audio personalizados en kbit/s.

---

## Archivos de salida

Los videos nunca se sobrescriben.

Ejemplo:

```text
video.mp4
video_compressed.mp4
video_compressed_1.mp4
video_compressed_2.mp4
```

---

## Tecnologías usadas

- Python
- FFmpeg
- interfaz de texto curses
- Termux en Android

---

## Autor

Proyecto educativo para compresión de video en Android usando herramientas libres.

- Washington Indacochea Delgado

Bajo [Licencia GPL3](LICENSE)

---

Dios te bendiga

---
