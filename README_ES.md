# FFmpeg Video Compressor TUI (Termux) - v3

Compresor de videos para **Android usando Termux**, hecho en **Python + FFmpeg + interfaz de texto (curses)**.

Este programa permite reducir el tamaño de un video ajustando calidad, resolución y audio, ideal para compartir por WhatsApp, Telegram u otras apps.
Al iniciar permite elegir idioma: **English** por defecto o **Español**.

# Caso de uso
Yo tengo un vídeo en mi celular de 900 MB que lo quería subir a WhatsApp, pero este me mostró un mensaje que decía que WhatsApp lo iba a recortar hasta dejarlo en 180MB (tenía de duración 10 minutos y si hacía eso lo iba a dejar en menos tiempo), y con este programa lo dejé a menos de 180 MB observando el tamaño aproximado al que iba quedando cuando le iba ajustando los parámetros, y lo comprimí y lo pude enviar completo y WhatsApp no me preguntó nada (o sea no fue necesario recortar el vídeo a menos de 10 minutos, sino que, reduciendo su tamaño a menos de 180 MB pude enviarlo completo).

---

## ¿Qué es este programa?

Es una aplicación que funciona **dentro de la terminal** (no tiene ventanas gráficas) y permite:

✅ Elegir idioma al iniciar: inglés o español  
✅ Buscar videos con un selector de archivos dentro de Termux  
✅ Cambiar resolución del vídeo  
✅ Ajustar calidad de video y audio (bitrate)  
✅ Ver el tamaño estimado aproximado final  
✅ Abrir una ayuda integrada de Termux  
✅ Comprimir el video  

---

## ¿Qué necesitas antes?

Este programa está pensado para **Android + Termux**.

### 1️⃣ Instalar Termux

Desde F-Droid

o:

Algunos celulares de la marca Xiaomi tienen una versión actualizada y full de Termux.

### 2️⃣ Instalar dependencias dentro de Termux

Abre Termux y escribe:

```bash
pkg update
pkg upgrade
pkg install git python ffmpeg
```

luego poner:

```bash
termux-setup-storage
```

Ese último comando permite acceder a la memoria del teléfono.

---

## Cómo ejecutar el programa

1. Clona (ya tenemos git instalado) o descarga este repositorio
2. Entra a esa carpeta desde Termux.
3. Ejecuta:

```bash
python ffmpegcompressor.py
```

Al abrir, primero aparece el selector de idioma. **English** aparece seleccionado por defecto; usa las flechas para elegir **Español** si lo prefieres y presiona **Enter**.

## Acceder al Almacenamiento Interno

Para que Termux tenga acceso a su almacenamiento interno, escriba:

```
termux-setup-storage
```

y presione Enter y acepte.

Para clonar un repositorio en la memoria interna primero hay que llegar allí. En Termux escriba:

```
cd storage
```

Luego escriba:

```
ls
```

para ver los repositorios disponibles.

Luego elija la memoria compartida:

```
cd shared
```

Comando especial: También se pueden abreviar esos dos pasos solo con:

```bash
cd /sdcard
```

Con cualquiera de los dos métodos llegará a la memoria interna compartida.

Para saber en qué ruta está ubicado, escriba en Termux:

```bash
pwd
```

y presione Enter.

**Nota**: Si es la primera vez que abre Termux estará en la carpeta de configuraciones de Termux (es una especie de emulación del HOME de Linux para que Termux tenga allí sus archivos como si estuviera en Linux):

```
/data/data/com.termux/files/home
```

y si ya está en la memoria interna y para llegar allí usó cd shared aparece así:

```
~/storage/shared $
```
y si uso: cd /sdcard así:
```
/sdcard $
```

>**Nota**: Siempre es importante saber dónde está ubicado porque puede ser que sin querer clonó un repositorio dentro del espacio de configuraciones de Termux o en storage, y en caso de pasar algún día eso, puede usar el comando mover "mv" para mover la carpeta que haya clonado desde el espacio de las configuraciones de Termux a storage y luego usar otra vez "mv" para mover la carpeta a "shared". Para esto es necesario saber que si estoy en "/data/data/com.termux/files/home" (que es por defecto donde uno está ubicado cuando recién abre Termux) fuera de este está "storage", y si estoy en "storage" fuera de este está "shared", entonces si cloné un repo llamado "mirepo" estando en ".../home" primero debo pasarlo a "storage" poniendo allí: `mv su-repo storage` y luego para pasarlo al Almacenamiento Interno poner: `mv su-repo shared` y listo solucionado; y si solo por error lo clonó en storage solo ponga: `mv su-repo shared`. Por cierto, si usted está en "shared" y desea ir a ".../home" ponga `cd`.

## 📸 Captura de pantalla

![Interfaz del compresor en Termux](images/20260621_141116_Termux.jpg)

## Ayuda integrada (Opcional)

En el menú principal, baja con las flechas hasta:

```text
Ayuda Termux: termux-setup-storage | Enter ver
```

Presiona **Enter** para abrir una ayuda dentro de la terminal. Allí se explica:

* Para qué sirve `termux-setup-storage`
* Rutas útiles como `/storage/emulated/0/`, `Download` y `/sdcard/`
* Dependencias necesarias
* Teclas principales del compresor
* Archivos locales de configuración

Para volver al menú principal, presiona cualquier tecla.

![Ayuda Termux](images/20260621_171214_Help_Termux.jpg)

---

## Controles del programa

| Tecla     | Función                                  |
| --------- | ---------------------------------------- |
| ↑ ↓       | Mover entre opciones                     |
| ← →       | Bajar/subir el valor marcado             |
| **Enter** | Elegir/editar la opción marcada          |
| **c**     | Recalcular tamaño estimado               |
| **f**     | Buscar video con selector de archivos    |
| **r**     | Comprimir video / iniciar proceso        |
| **s**     | Detener mientras está comprimiendo       |
| **q**     | Salir                                    |

---

## Cómo cargar el video

Al iniciar, después de elegir idioma, aparece un selector de archivos.

Puedes navegar con las flechas:

* **↑ ↓**: moverse por carpetas y videos
* **Enter**: abrir carpeta o elegir video
* **q** o **ESC**: cancelar

Una forma simple de usarlo es colocar el video en la carpeta del repositorio:

```text
whatsapp-termux-video-compressor
```

Luego abre el programa y selecciona el video desde el selector.

También puedes acceder a carpetas del teléfono si ya ejecutaste:

```bash
termux-setup-storage
```

Después de elegir el video, presiona **c** para recalcular el tamaño estimado si cambias parámetros, **r** para iniciar la compresión y **s** para detenerla mientras está comprimiendo.

---

## Parámetros que puedes cambiar

En los valores numéricos, **←** disminuye y **→** aumenta. Esto aplica a bitrate de video, framerate, canales de audio, bitrate de audio y frecuencia de audio.

### Escala

Cambia la resolución del video:

* Horizontal / Landscape → formato normal
* Vertical / Portrait → para videos tipo TikTok / Reels

En **Escala**, las flechas izquierda/derecha alternan entre las opciones disponibles.

Cuando la opción **Escala / Scale** está marcada, puedes cambiar entre `scale=512:288` y `scale=288:512` con **← →** o presionando **Enter**.

### Bitrate de video

Controla la calidad del video.
Más alto = mejor calidad = archivo más grande.

### Audio

Puedes cambiar:

* Canales (mono o estéreo)
* Bitrate de audio
* Frecuencia (sample rate)

---

## Por qué esos valores por defecto

El programa inicia con estos valores:

| Parámetro | Valor por defecto | Motivo práctico |
| --------- | ----------------- | --------------- |
| Escala | `scale=512:288` | Baja la resolución para reducir mucho el peso del video. |
| Bitrate video | `200k` | Mantiene una calidad aceptable para pantalla de teléfono sin hacer el archivo muy grande. |
| Framerate | `15` | Reduce la cantidad de cuadros por segundo y baja el tamaño final. |
| Canales audio | `1` | Usa audio mono; para voz o videos casuales suele ser suficiente y pesa menos que estéreo. |
| Bitrate audio | `64k` | Da más margen de calidad que las pruebas antiguas de 18k-30k, pero sigue siendo liviano. |
| Sample rate | `44100 Hz` | Es una frecuencia común y compatible para audio. |

Estos valores vienen de pruebas manuales antiguas hechas con FFmpeg/FFmulticonverter para poder enviar videos por WhatsApp cuando el límite era mucho más pequeño, alrededor de **16 MB**. En esas pruebas se usaban comandos como:

```bash
-vf "scale=512:288" -b:v 200k -r 15 -ac 1 -b:a 30k -ar 44100
```

La idea era siempre la misma:

* Reducir la resolución con `scale=512:288`.
* Bajar el bitrate de video para controlar el tamaño.
* Usar `15 fps` para reducir cuadros por segundo.
* Convertir el audio a mono con `-ac 1`.
* Usar un bitrate de audio bajo.
* Mantener `44100 Hz` por compatibilidad.

Hoy WhatsApp permite enviar videos de mayor tamaño, por eso este programa usa valores un poco más cómodos, especialmente en audio (`64k` en vez de 18k-30k). Aun así, los valores por defecto siguen siendo un buen punto de partida porque comprimen bastante sin obligarte a calcular todo desde cero.

Si el video queda muy grande, baja primero el **bitrate de video**. Si todavía necesitas reducir más, prueba bajar el **bitrate de audio** o usar un valor de video más bajo. Después presiona **c** para recalcular el tamaño estimado.

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

## ¿Cuántos formatos de video acepta este programa?

Realmente **no limita formatos**.
Quien manda aquí es **FFmpeg**.

FFmpeg Acepta **casi todos los formatos de video que existen**.

### 📌 Ejemplos de formatos que FFmpeg suele soportar:

| Tipo        | Formatos comunes         |
| ----------- | ------------------------ |
| 📱 Móvil    | MP4, 3GP, MOV            |
| 💻 PC       | AVI, MKV, WMV            |
| 🌐 Internet | WEBM, FLV                |
| 📺 TV/HD    | MPEG, MPG, TS, MTS, M2TS |
| 🎥 Cámaras  | MOV, MTS, MXF            |

---

### ¿Por qué acepta tantos?

Porque el programa solo hace:

```bash
ffmpeg -i archivo
```

Y FFmpeg detecta el formato automáticamente.

---

## Cálculo de tamaño estimado

El programa calcula cuánto pesará el video antes de comprimir.

Además, aprende con el tiempo usando:

```
correction_factor.json
```

Cada conversión mejora la precisión del cálculo.

Formato:

```json
{
  "factor": 1.08,
  "n": 0
}
```

* `factor`: multiplicador usado para ajustar la estimación.
* `n`: cantidad de conversiones usadas para calcular ese factor.

Este archivo no se sube a GitHub porque es generado por el programa y depende de las conversiones hechas en cada teléfono.

---

## Archivos locales ignorados

Estos archivos se guardan localmente, pero están excluidos en `.gitignore`:

```text
correction_factor.json
custom_bitrates.json
```

La razón es que ambos contienen datos generados o preferencias personales del usuario:

* `correction_factor.json`: cambia después de comprimir videos y ajusta la estimación según resultados reales.
* `custom_bitrates.json`: guarda bitrates manuales agregados por el usuario.

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

* `video`: lista de bitrates de video personalizados en kbit/s.
* `audio`: lista de bitrates de audio personalizados en kbit/s.

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

## Autor

Proyecto educativo para compresión de video en Android usando herramientas libres.

- Washington Indacochea Delgado

---
