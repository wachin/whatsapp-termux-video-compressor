#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpegCompressor (curses / Termux-friendly) — v3

- Curses TUI for Termux (no GUI)
- Keeps selectable parameters:
  Escala, Bitrate video, Framerate, Canales audio, Bitrate audio, Sample rate
- Calculates estimated output size using ffprobe duration + correction_factor.json
- Runs ffmpeg and streams output in a scrolling window
- Stop conversion with key 's'
- Manual bitrate entry for video/audio (Enter) and persists manual values in JSON
- Output filename uses an incremental suffix to avoid overwriting / re-encoding issues

Requirements (Termux):
  pkg install ffmpeg python
Recommended:
  termux-setup-storage
"""

from __future__ import annotations

import curses
import curses.textpad
import json
import os
import shlex
import signal
import subprocess
import textwrap
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple


DEFAULT_CORRECTION_FACTOR = 1.08
CORRECTION_FILE = "correction_factor.json"
CUSTOM_BITRATES_FILE = "custom_bitrates.json"

SCALE_OPTIONS = [
    "scale=512:288 Horizontal",
    "scale=288:512 Vertical",
]
SCALE_LABELS = {
    "en": [
        "scale=512:288 Landscape",
        "scale=288:512 Portrait",
    ],
    "es": [
        "scale=512:288 Horizontal",
        "scale=288:512 Vertical",
    ],
}

TEXT = {
    "en": {
        "lang_title": "Select Language",
        "lang_footer": "↑↓ move | Enter select | q/ESC quit",
        "help_title": "Termux Help",
        "help_back": "Press any key to return.",
        "help_scroll_footer": "↑↓ scroll | q/ESC/Enter return",
        "help_lines": [
            "Quick use",
            "  Arrows: move through options.",
            "  Enter: edit/select the highlighted option.",
            "  c: recalculate estimated size.",
            "  r: compress / start process.",
            "  s: stop while ffmpeg is compressing.",
            "  q: exit the compressor.",
            "",
            "Why these defaults",
            "  The defaults come from old WhatsApp compression tests made when videos had to stay under about 16 MB.",
            "  512x288, 15 fps, mono audio and low bitrates reduce size aggressively while keeping the video usable.",
            "  Today WhatsApp allows larger files, so these values are only a practical starting point.",
            "",
            "Local files",
            f"  {CUSTOM_BITRATES_FILE}: saved manual bitrates.",
            f"  {CORRECTION_FILE}: estimate adjustment from real results.",
        ],
        "path_prompt": "File path (paste or type):",
        "browser_title": "Select video",
        "folder": "Folder",
        "empty_browser": "(no folders or supported videos)",
        "browser_footer": "↑↓ move | Enter open/select | q/ESC cancel",
        "int_prompt": "Type a number ({min_v}–{max_v}) and press Enter:",
        "esc_cancel": "ESC = cancel",
        "missing_input": "File not found.",
        "missing_ffprobe": "ffprobe was not found. In Termux: pkg install ffmpeg",
        "ffprobe_failed": "ffprobe failed. Is ffprobe/ffmpeg installed in Termux?",
        "run_title": "FFmpeg Compressor (curses) — Running",
        "no_valid_file": "No valid file. Press any key to return.",
        "command": "Command:",
        "keys": "Keys: ",
        "run_keys": "s=Stop   q=Back (stops first if running)",
        "missing_ffmpeg": "ffmpeg was not found. In Termux: pkg install ffmpeg",
        "ffmpeg_start_error": "Could not run ffmpeg: {error}",
        "result_title": "FFmpeg Compressor (curses) — Result",
        "stopped": "Status: Process stopped by user.",
        "success": "Status: Success. Compressed video saved.",
        "output": "Output",
        "correction_updated": "Correction factor updated: {factor:.4f} (n={n})",
        "real_size": "Real size: {size:.2f} MB",
        "correction_failed": "Could not update factor: {error}",
        "failed": "Status: Failed (code {code}).",
        "check_output": "Check the previous output (ffmpeg).",
        "back_menu": "Press any key to return to the menu.",
        "main_title": "FFmpeg Video Compressor — Termux (curses)",
        "main_nav": "↑↓ move | Enter select/edit",
        "input_file": "Input file",
        "scale": "Scale",
        "video_bitrate": "Video bitrate (k)",
        "framerate": "Framerate",
        "audio_channels": "Audio channels",
        "audio_bitrate": "Audio bitrate (k)",
        "sample_rate": "Sample rate",
        "empty": "(empty)",
        "estimated_size_na": "Estimated size: N/A",
        "estimated_size": "Estimated size: {size:.2f} MB",
        "correction_factor": "Correction factor: {factor:.4f} (n={n})",
        "custom_bitrates": "Manual bitrates saved in: {file}",
        "help_c": "• c: recalculate estimated size",
        "help_arrows": "• ←/→: change scale or selected value",
        "help_r": "• r: compress / start process",
        "help_s": "• s: stop while compressing",
        "help_q": "• q: exit",
        "termux_footer": "Termux Help build in | Enter view",
        "video_bitrate_title": "Video bitrate (kbit/s)",
        "audio_bitrate_title": "Audio bitrate (kbit/s)",
        "error": "Error",
    },
    "es": {
        "lang_title": "Seleccionar idioma",
        "lang_footer": "↑↓ mover | Enter elegir | q/ESC salir",
        "help_title": "Ayuda Termux",
        "help_back": "Presiona cualquier tecla para volver.",
        "help_scroll_footer": "↑↓ desplazar | q/ESC/Enter volver",
        "help_lines": [
            "Uso rapido",
            "  Flechas: moverse por las opciones.",
            "  Enter: editar/elegir la opcion marcada.",
            "  c: recalcular tamaño estimado.",
            "  r: comprimir / iniciar proceso.",
            "  s: detener mientras ffmpeg esta comprimiendo.",
            "  q: salir del compresor.",
            "",
            "Por que estos valores",
            "  Los valores por defecto vienen de pruebas antiguas para WhatsApp, cuando los videos debian quedar por debajo de unos 16 MB.",
            "  512x288, 15 fps, audio mono y bitrates bajos reducen bastante el tamaño sin dejar el video inutilizable.",
            "  Hoy WhatsApp permite archivos mas grandes, asi que estos valores son solo un punto de partida practico.",
            "",
            "Archivos locales",
            f"  {CUSTOM_BITRATES_FILE}: bitrates manuales guardados.",
            f"  {CORRECTION_FILE}: ajuste del calculo segun resultados reales.",
        ],
        "path_prompt": "Ruta del archivo (pega o escribe):",
        "browser_title": "Seleccionar video",
        "folder": "Carpeta",
        "empty_browser": "(sin carpetas ni videos soportados)",
        "browser_footer": "↑↓ mover | Enter abrir/elegir | q/ESC cancelar",
        "int_prompt": "Escribe un número ({min_v}–{max_v}) y presiona Enter:",
        "esc_cancel": "ESC = cancelar",
        "missing_input": "Archivo no encontrado.",
        "missing_ffprobe": "No se encontró ffprobe. En Termux: pkg install ffmpeg",
        "ffprobe_failed": "ffprobe falló. ¿Existe ffprobe/ffmpeg en Termux?",
        "run_title": "Compresor FFmpeg (curses) — Ejecutando",
        "no_valid_file": "No hay archivo válido. Presiona cualquier tecla para volver.",
        "command": "Comando:",
        "keys": "Teclas: ",
        "run_keys": "s=Detener   q=Volver (si está corriendo, detiene primero)",
        "missing_ffmpeg": "No se encontró ffmpeg. En Termux: pkg install ffmpeg",
        "ffmpeg_start_error": "No se pudo ejecutar ffmpeg: {error}",
        "result_title": "Compresor FFmpeg (curses) — Resultado",
        "stopped": "Estado: Proceso detenido por el usuario.",
        "success": "Estado: Éxito. Video comprimido guardado.",
        "output": "Salida",
        "correction_updated": "Factor de corrección actualizado: {factor:.4f} (n={n})",
        "real_size": "Tamaño real: {size:.2f} MB",
        "correction_failed": "No se pudo actualizar el factor: {error}",
        "failed": "Estado: Falló (código {code}).",
        "check_output": "Revisa la salida anterior (ffmpeg).",
        "back_menu": "Presiona cualquier tecla para volver al menú.",
        "main_title": "Compresor de Video FFmpeg — Termux (curses)",
        "main_nav": "↑↓ mover | Enter elegir/editar",
        "input_file": "Archivo de entrada",
        "scale": "Escala",
        "video_bitrate": "Bitrate video (k)",
        "framerate": "Fotogramas/s",
        "audio_channels": "Canales audio",
        "audio_bitrate": "Bitrate audio (k)",
        "sample_rate": "Frecuencia audio",
        "empty": "(vacío)",
        "estimated_size_na": "Tamaño estimado: N/A",
        "estimated_size": "Tamaño estimado: {size:.2f} MB",
        "correction_factor": "Factor de corrección: {factor:.4f} (n={n})",
        "custom_bitrates": "Bitrates manuales guardados en: {file}",
        "help_c": "• c: recalcular tamaño estimado",
        "help_arrows": "• ←/→: cambiar escala o valor marcado",
        "help_r": "• r: comprimir / iniciar proceso",
        "help_s": "• s: detener mientras está comprimiendo",
        "help_q": "• q: salir",
        "termux_footer": "Ayuda Termux integrada | Enter ver",
        "video_bitrate_title": "Bitrate de video (kbit/s)",
        "audio_bitrate_title": "Bitrate de audio (kbit/s)",
        "error": "Error",
    },
}

# Requested fixed base lists
VIDEO_BITRATES_BASE = [550, 500, 450, 400, 350, 300, 250, 200, 180, 170, 160, 150, 145, 140, 130]
AUDIO_BITRATES_BASE = [320, 192, 160, 144, 128, 112, 96, 80, 64, 56, 48, 40]

FRAMERATES = [15, 24, 30]
AUDIO_CHANNELS = [1, 2]
SAMPLE_RATES = ["96000 Hz", "48000 Hz", "44100 Hz", "32000 Hz", "24000 Hz", "22050 Hz", "16000 Hz"]
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm", ".m4v",
    ".3gp", ".mpeg", ".mpg", ".ts", ".mts", ".m2ts",
}


def t(lang: str, key: str, **kwargs) -> str:
    text = TEXT.get(lang, TEXT["en"]).get(key, TEXT["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text


def scale_display(lang: str, idx: int) -> str:
    labels = SCALE_LABELS.get(lang, SCALE_LABELS["en"])
    return labels[idx]


def load_correction_factor() -> Tuple[float, int]:
    try:
        with open(CORRECTION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        factor = float(data.get("factor", DEFAULT_CORRECTION_FACTOR))
        n = int(data.get("n", 0))
        if factor <= 0:
            return DEFAULT_CORRECTION_FACTOR, 0
        return factor, max(n, 0)
    except FileNotFoundError:
        return DEFAULT_CORRECTION_FACTOR, 0
    except Exception:
        return DEFAULT_CORRECTION_FACTOR, 0


def save_correction_factor(factor: float, n: int) -> None:
    with open(CORRECTION_FILE, "w", encoding="utf-8") as f:
        json.dump({"factor": float(factor), "n": int(n)}, f)


def load_custom_bitrates() -> Tuple[List[int], List[int]]:
    """
    Returns (custom_video, custom_audio).
    """
    try:
        with open(CUSTOM_BITRATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        v = [int(x) for x in data.get("video", []) if str(x).isdigit()]
        a = [int(x) for x in data.get("audio", []) if str(x).isdigit()]
        # Filter nonsensical values
        v = [x for x in v if 10 <= x <= 50000]
        a = [x for x in a if 10 <= x <= 50000]
        return v, a
    except FileNotFoundError:
        return [], []
    except Exception:
        return [], []


def save_custom_bitrates(video: List[int], audio: List[int]) -> None:
    with open(CUSTOM_BITRATES_FILE, "w", encoding="utf-8") as f:
        json.dump({"video": video, "audio": audio}, f)


def merge_sorted_desc(base: List[int], extra: List[int]) -> List[int]:
    s = sorted(set(base).union(extra), reverse=True)
    return s


def insert_value_sorted_desc(values: List[int], v: int) -> int:
    """
    Insert value into list (if absent), keep sorted descending.
    Returns the index of the value in the updated list.
    """
    if v not in values:
        values.append(v)
        values.sort(reverse=True)
    return values.index(v)


def ffprobe_duration_seconds(input_file: str) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file,
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    return float(out)


def estimate_size_mb(duration_s: float, v_kbps: int, a_kbps: int, correction_factor: float) -> float:
    video_size = (v_kbps * 1000 * duration_s) / 8.0
    audio_size = (a_kbps * 1000 * duration_s) / 8.0
    total_mb = (video_size + audio_size) / (1024.0 * 1024.0)
    return total_mb * correction_factor


def get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024.0 * 1024.0)


def unique_output_path(input_file: str) -> str:
    """
    Generates a unique output filename:
      <base>_compressed.mp4
      <base>_compressed_1.mp4
      <base>_compressed_2.mp4 ...
    """
    base, _ext = os.path.splitext(input_file)
    candidate = base + "_compressed.mp4"
    if not os.path.exists(candidate):
        return candidate
    i = 1
    while True:
        candidate = f"{base}_compressed_{i}.mp4"
        if not os.path.exists(candidate):
            return candidate
        i += 1


def build_ffmpeg_command(input_file: str, scale_token: str, vbr: int, fr: int, ac: int, abr: int, sr: int) -> Tuple[List[str], str]:
    output_file = unique_output_path(input_file)
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-vf", scale_token,
        "-b:v", f"{vbr}k",
        "-r", str(fr),
        "-ac", str(ac),
        "-b:a", f"{abr}k",
        "-ar", str(sr),
        output_file,
    ]
    return cmd, output_file


def update_correction_with_result(estimated_mb: Optional[float], current_factor: float, current_n: int, output_file: str) -> Tuple[float, int]:
    if estimated_mb is None or estimated_mb <= 0 or current_factor <= 0 or not os.path.isfile(output_file):
        return current_factor, current_n
    real_size = get_file_size_mb(output_file)
    uncorrected_estimate = estimated_mb / current_factor
    if uncorrected_estimate <= 0:
        return current_factor, current_n
    observed_factor = real_size / uncorrected_estimate
    updated_factor = (current_factor * current_n + observed_factor) / (current_n + 1)
    return float(updated_factor), int(current_n + 1)


@dataclass
class AppState:
    input_file: str = ""
    scale_idx: int = 0
    vbr_idx: int = 0
    fr_idx: int = 0
    ac_idx: int = 0
    abr_idx: int = 0
    sr_idx: int = 0

    estimated_mb: Optional[float] = None
    correction_factor: float = DEFAULT_CORRECTION_FACTOR
    correction_n: int = 0
    last_error: str = ""

    def scale_token(self) -> str:
        return SCALE_OPTIONS[self.scale_idx].split()[0]


def safe_addstr(win, y: int, x: int, s: str, attr: int = 0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h:
        return
    if x < 0:
        s = s[-x:]
        x = 0
    if x >= w:
        return
    win.addnstr(y, x, s, max(0, w - x - 1), attr)


def draw_header(stdscr, title: str):
    h, w = stdscr.getmaxyx()
    stdscr.attron(curses.A_BOLD)
    stdscr.addnstr(0, 2, title, max(0, w - 4))
    stdscr.attroff(curses.A_BOLD)
    stdscr.hline(1, 0, curses.ACS_HLINE, w)


def draw_footer(stdscr, msg: str, attr: int = 0):
    h, w = stdscr.getmaxyx()
    stdscr.hline(h - 2, 0, curses.ACS_HLINE, w)
    stdscr.addnstr(h - 1, 2, msg, max(0, w - 4), attr)


def wrap_help_lines(lines: List[str], width: int) -> List[Tuple[str, bool]]:
    wrapped = []
    max_width = max(20, width)
    for line in lines:
        if not line:
            wrapped.append(("", False))
            continue

        is_heading = not line.startswith(" ")
        indent = len(line) - len(line.lstrip(" "))
        prefix = " " * indent
        text = line.strip()

        for part in textwrap.wrap(text, width=max_width - indent, break_long_words=False) or [""]:
            wrapped.append((prefix + part, is_heading))
            is_heading = False
    return wrapped


def show_termux_help(stdscr, lang: str) -> None:
    lines = TEXT.get(lang, TEXT["en"])["help_lines"]
    top = 0

    while True:
        stdscr.erase()
        draw_header(stdscr, t(lang, "help_title"))
        h, w = stdscr.getmaxyx()
        available = max(0, h - 5)
        wrapped = wrap_help_lines(lines, max(20, w - 4))
        max_top = max(0, len(wrapped) - available)
        top = min(top, max_top)

        for i, (line, is_heading) in enumerate(wrapped[top:top + available]):
            attr = curses.A_BOLD if line and is_heading else 0
            safe_addstr(stdscr, 3 + i, 2, line, attr)

        footer = t(lang, "help_scroll_footer") if max_top else t(lang, "help_back")
        draw_footer(stdscr, footer)
        stdscr.refresh()

        ch = stdscr.getch()
        if ch == curses.KEY_UP:
            if top > 0:
                top -= 1
        elif ch == curses.KEY_DOWN:
            if top < max_top:
                top += 1
        elif ch in (ord("q"), ord("Q"), 27, 10, 13, curses.KEY_ENTER):
            return


def edit_text_popup(stdscr, title: str, initial: str, lang: str) -> Optional[str]:
    h, w = stdscr.getmaxyx()
    ph = 7
    pw = min(max(50, len(initial) + 10), max(20, w - 4))
    y = (h - ph) // 2
    x = (w - pw) // 2
    win = curses.newwin(ph, pw, y, x)
    win.border()
    safe_addstr(win, 0, 2, f" {title} ", curses.A_BOLD)
    safe_addstr(win, 2, 2, t(lang, "path_prompt"))

    box = curses.newwin(1, pw - 4, y + 4, x + 2)
    box.addnstr(0, 0, initial, max(0, pw - 5))
    curses.curs_set(1)
    tb = curses.textpad.Textbox(box)

    def validator(ch):
        if ch == 27:  # ESC
            return 7  # Ctrl+G
        if ch in (10, 13):  # Enter
            return 7
        return ch

    s = tb.edit(validator).strip()
    curses.curs_set(0)
    if not s:
        return None
    return s


def select_language(stdscr) -> Optional[str]:
    options = [("en", "English"), ("es", "Español")]
    idx = 0

    while True:
        stdscr.erase()
        draw_header(stdscr, "Select Language / Seleccionar idioma")
        safe_addstr(stdscr, 3, 2, "Default: English", curses.A_DIM)

        for row, (_lang, label) in enumerate(options):
            attr = curses.A_REVERSE if row == idx else 0
            safe_addstr(stdscr, 5 + row, 4, label, attr)

        draw_footer(stdscr, "↑↓ move/mover | Enter select/elegir | q/ESC quit/salir")
        stdscr.refresh()

        ch = stdscr.getch()
        if ch in (ord("q"), ord("Q"), 27):
            return None
        if ch == curses.KEY_UP:
            idx = (idx - 1) % len(options)
        elif ch == curses.KEY_DOWN:
            idx = (idx + 1) % len(options)
        elif ch in (10, 13, curses.KEY_ENTER):
            return options[idx][0]


def list_video_browser_entries(directory: str) -> Tuple[List[Tuple[str, str]], Optional[str]]:
    entries: List[Tuple[str, str]] = []
    error = None
    try:
        with os.scandir(directory) as scan:
            for entry in scan:
                try:
                    if entry.is_dir():
                        entries.append((entry.name + "/", entry.path))
                    elif entry.is_file() and os.path.splitext(entry.name)[1].lower() in VIDEO_EXTENSIONS:
                        entries.append((entry.name, entry.path))
                except OSError:
                    continue
    except OSError as e:
        error = str(e)

    entries.sort(key=lambda item: (not item[0].endswith("/"), item[0].lower()))
    parent = os.path.dirname(os.path.abspath(directory))
    if parent and parent != os.path.abspath(directory):
        entries.insert(0, ("../", parent))
    return entries, error


def pick_video_file(stdscr, start_path: str, lang: str) -> Optional[str]:
    current_dir = os.path.abspath(os.path.expanduser(start_path or os.getcwd()))
    if os.path.isfile(current_dir):
        current_dir = os.path.dirname(current_dir)
    elif not os.path.isdir(current_dir):
        current_dir = os.getcwd()

    idx = 0
    top = 0
    last_error = None

    while True:
        entries, error = list_video_browser_entries(current_dir)
        last_error = error
        if idx >= len(entries):
            idx = max(0, len(entries) - 1)

        stdscr.erase()
        draw_header(stdscr, t(lang, "browser_title"))
        h, w = stdscr.getmaxyx()
        safe_addstr(stdscr, 2, 2, f"{t(lang, 'folder')}: {current_dir}", curses.A_BOLD)
        if last_error:
            safe_addstr(stdscr, 3, 2, f"{t(lang, 'error')}: {last_error}", curses.A_BOLD)

        list_y = 4
        visible = max(1, h - 7)
        if idx < top:
            top = idx
        elif idx >= top + visible:
            top = idx - visible + 1

        if not entries:
            safe_addstr(stdscr, list_y, 2, t(lang, "empty_browser"))
        else:
            for row, (label, path) in enumerate(entries[top:top + visible]):
                attr = curses.A_REVERSE if top + row == idx else 0
                prefix = "[D] " if os.path.isdir(path) else "[V] "
                safe_addstr(stdscr, list_y + row, 2, prefix + label, attr)

        draw_footer(stdscr, t(lang, "browser_footer"))
        stdscr.refresh()

        ch = stdscr.getch()
        if ch in (ord("q"), ord("Q"), 27):
            return None
        if ch == curses.KEY_UP and entries:
            idx = (idx - 1) % len(entries)
        elif ch == curses.KEY_DOWN and entries:
            idx = (idx + 1) % len(entries)
        elif ch in (10, 13, curses.KEY_ENTER) and entries:
            _label, selected = entries[idx]
            if os.path.isdir(selected):
                current_dir = selected
                idx = 0
                top = 0
                last_error = None
            else:
                return selected


def edit_int_popup(stdscr, title: str, initial: int, lang: str, min_v: int = 10, max_v: int = 50000) -> Optional[int]:
    h, w = stdscr.getmaxyx()
    ph = 9
    pw = min(60, max(20, w - 4))
    y = (h - ph) // 2
    x = (w - pw) // 2
    win = curses.newwin(ph, pw, y, x)
    win.border()
    safe_addstr(win, 0, 2, f" {title} ", curses.A_BOLD)
    safe_addstr(win, 2, 2, t(lang, "int_prompt", min_v=min_v, max_v=max_v))
    safe_addstr(win, 3, 2, t(lang, "esc_cancel"))

    box = curses.newwin(1, pw - 4, y + 5, x + 2)
    box.addnstr(0, 0, str(initial), max(0, pw - 5))
    curses.curs_set(1)
    tb = curses.textpad.Textbox(box)

    def validator(ch):
        if ch == 27:  # ESC
            return 7
        if ch in (10, 13):  # Enter
            return 7
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            return ch
        if 0 <= ch <= 255 and chr(ch).isdigit():
            return ch
        return 0

    raw = tb.edit(validator).strip()
    curses.curs_set(0)

    if not raw or not raw.isdigit():
        return None
    val = int(raw)
    if val < min_v or val > max_v:
        return None
    return val


def calc_estimate(state: AppState, video_bitrates: List[int], audio_bitrates: List[int], lang: str) -> None:
    state.last_error = ""
    if not state.input_file:
        state.estimated_mb = None
        return
    if not os.path.isfile(state.input_file):
        state.estimated_mb = None
        state.last_error = t(lang, "missing_input")
        return
    try:
        dur = ffprobe_duration_seconds(state.input_file)
        v_kbps = int(video_bitrates[state.vbr_idx])
        a_kbps = int(audio_bitrates[state.abr_idx])
        state.estimated_mb = estimate_size_mb(dur, v_kbps, a_kbps, state.correction_factor)
    except FileNotFoundError:
        state.estimated_mb = None
        state.last_error = t(lang, "missing_ffprobe")
    except subprocess.CalledProcessError:
        state.estimated_mb = None
        state.last_error = t(lang, "ffprobe_failed")
    except Exception as e:
        state.estimated_mb = None
        state.last_error = str(e)


def run_ffmpeg_screen(stdscr, state: AppState, video_bitrates: List[int], audio_bitrates: List[int], lang: str) -> None:
    stdscr.clear()
    draw_header(stdscr, t(lang, "run_title"))
    h, w = stdscr.getmaxyx()

    if not state.input_file or not os.path.isfile(state.input_file):
        draw_footer(stdscr, t(lang, "no_valid_file"))
        stdscr.refresh()
        stdscr.getch()
        return

    scale = state.scale_token()
    vbr = int(video_bitrates[state.vbr_idx])
    fr = int(FRAMERATES[state.fr_idx])
    ac = int(AUDIO_CHANNELS[state.ac_idx])
    abr = int(audio_bitrates[state.abr_idx])
    sr = int(SAMPLE_RATES[state.sr_idx].split()[0])

    cmd, output_file = build_ffmpeg_command(state.input_file, scale, vbr, fr, ac, abr, sr)

    out_h = h - 6
    out_w = w - 4
    out_win = curses.newwin(out_h, out_w, 3, 2)
    out_win.scrollok(True)
    out_win.idlok(True)
    out_win.border()

    safe_addstr(stdscr, 2, 2, t(lang, "command"), curses.A_BOLD)
    safe_addstr(stdscr, 2, 11, " ".join(shlex.quote(arg) for arg in cmd)[: max(0, w - 12)])
    safe_addstr(stdscr, h - 3, 2, t(lang, "keys"), curses.A_BOLD)
    safe_addstr(stdscr, h - 3, 10, t(lang, "run_keys"))

    stdscr.refresh()
    out_win.refresh()

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )
    except FileNotFoundError:
        draw_footer(stdscr, t(lang, "missing_ffmpeg"))
        stdscr.refresh()
        stdscr.getch()
        return
    except Exception as e:
        draw_footer(stdscr, t(lang, "ffmpeg_start_error", error=e))
        stdscr.refresh()
        stdscr.getch()
        return

    stdscr.nodelay(True)
    stopped = False

    def stop_process():
        nonlocal stopped
        if proc.poll() is not None:
            return
        stopped = True
        try:
            if hasattr(os, "killpg"):
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass

    while True:
        ch = stdscr.getch()
        if ch in (ord('s'), ord('S')):
            stop_process()
        if ch in (ord('q'), ord('Q')):
            if proc.poll() is None:
                stop_process()
                time.sleep(0.3)
            break

        line = None
        if proc.stdout is not None:
            line = proc.stdout.readline()
        if line:
            try:
                out_win.addnstr(line.rstrip("\n"), max(0, out_w - 2))
                out_win.addstr("\n")
            except curses.error:
                pass
            out_win.refresh()
        else:
            if proc.poll() is not None:
                break
            time.sleep(0.02)

    stdscr.nodelay(False)
    rc = proc.poll()
    if rc is None:
        stop_process()
        try:
            proc.wait(timeout=2)
        except Exception:
            pass
        rc = proc.poll()

    stdscr.clear()
    draw_header(stdscr, t(lang, "result_title"))

    if stopped:
        safe_addstr(stdscr, 3, 2, t(lang, "stopped"), curses.A_BOLD)
    elif rc == 0:
        safe_addstr(stdscr, 3, 2, t(lang, "success"), curses.A_BOLD)
        safe_addstr(stdscr, 5, 2, f"{t(lang, 'output')}: {output_file}")
        try:
            # Update correction factor (and persist)
            new_factor, new_n = update_correction_with_result(state.estimated_mb, state.correction_factor, state.correction_n, output_file)
            state.correction_factor, state.correction_n = new_factor, new_n
            save_correction_factor(state.correction_factor, state.correction_n)
            safe_addstr(stdscr, 7, 2, t(lang, "correction_updated", factor=state.correction_factor, n=state.correction_n))
            safe_addstr(stdscr, 8, 2, t(lang, "real_size", size=get_file_size_mb(output_file)))
        except Exception as e:
            safe_addstr(stdscr, 7, 2, t(lang, "correction_failed", error=e))
    else:
        safe_addstr(stdscr, 3, 2, t(lang, "failed", code=rc), curses.A_BOLD)
        safe_addstr(stdscr, 5, 2, t(lang, "check_output"))

    draw_footer(stdscr, t(lang, "back_menu"))
    stdscr.refresh()
    stdscr.getch()


def main_screen(stdscr) -> None:
    curses.curs_set(0)
    curses.use_default_colors()
    stdscr.keypad(True)

    lang = select_language(stdscr)
    if lang is None:
        return

    # Load persistent values
    state = AppState()
    state.correction_factor, state.correction_n = load_correction_factor()

    custom_v, custom_a = load_custom_bitrates()
    video_bitrates = merge_sorted_desc(VIDEO_BITRATES_BASE, custom_v)
    audio_bitrates = merge_sorted_desc(AUDIO_BITRATES_BASE, custom_a)

    # Set sane defaults
    state.vbr_idx = video_bitrates.index(200) if 200 in video_bitrates else 0
    state.abr_idx = audio_bitrates.index(64) if 64 in audio_bitrates else 0
    state.fr_idx = FRAMERATES.index(15) if 15 in FRAMERATES else 0
    state.ac_idx = AUDIO_CHANNELS.index(1) if 1 in AUDIO_CHANNELS else 0
    state.sr_idx = SAMPLE_RATES.index("44100 Hz") if "44100 Hz" in SAMPLE_RATES else 0

    selected = pick_video_file(stdscr, os.getcwd(), lang)
    if selected is None:
        return
    state.input_file = selected

    calc_estimate(state, video_bitrates, audio_bitrates, lang)

    fields = [
        (t(lang, "input_file"), "input"),
        (t(lang, "scale"), "scale"),
        (t(lang, "video_bitrate"), "vbr"),
        (t(lang, "framerate"), "fr"),
        (t(lang, "audio_channels"), "ac"),
        (t(lang, "audio_bitrate"), "abr"),
        (t(lang, "sample_rate"), "sr"),
    ]
    idx = 0
    help_idx = len(fields)

    while True:
        stdscr.erase()
        draw_header(stdscr, t(lang, "main_title"))

        h, w = stdscr.getmaxyx()
        safe_addstr(stdscr, 2, 2, t(lang, "main_nav"), curses.A_DIM)

        y0 = 3
        for i, (label, key) in enumerate(fields):
            attr = curses.A_REVERSE if i == idx else 0
            safe_addstr(stdscr, y0 + i, 2, f"{label:16}:", (attr | curses.A_BOLD) if i == idx else curses.A_BOLD)

            if key == "input":
                val = os.path.basename(state.input_file) if state.input_file else t(lang, "empty")
            elif key == "scale":
                val = scale_display(lang, state.scale_idx)
            elif key == "vbr":
                val = str(video_bitrates[state.vbr_idx])
            elif key == "fr":
                val = str(FRAMERATES[state.fr_idx])
            elif key == "ac":
                val = str(AUDIO_CHANNELS[state.ac_idx])
            elif key == "abr":
                val = str(audio_bitrates[state.abr_idx])
            elif key == "sr":
                val = SAMPLE_RATES[state.sr_idx]
            else:
                val = ""

            safe_addstr(stdscr, y0 + i, 22, val, attr)

        est_line = t(lang, "estimated_size_na")
        if state.estimated_mb is not None:
            est_line = t(lang, "estimated_size", size=state.estimated_mb)
        safe_addstr(stdscr, y0 + len(fields) + 1, 2, est_line, curses.A_BOLD)

        safe_addstr(stdscr, y0 + len(fields) + 2, 2, t(lang, "correction_factor", factor=state.correction_factor, n=state.correction_n))
        safe_addstr(stdscr, y0 + len(fields) + 3, 2, t(lang, "custom_bitrates", file=CUSTOM_BITRATES_FILE), curses.A_DIM)
        safe_addstr(stdscr, y0 + len(fields) + 4, 2, t(lang, "help_c"), curses.A_DIM)
        safe_addstr(stdscr, y0 + len(fields) + 5, 2, t(lang, "help_arrows"), curses.A_DIM)
        safe_addstr(stdscr, y0 + len(fields) + 6, 2, t(lang, "help_r"), curses.A_DIM)
        safe_addstr(stdscr, y0 + len(fields) + 7, 2, t(lang, "help_s"), curses.A_DIM)
        safe_addstr(stdscr, y0 + len(fields) + 8, 2, t(lang, "help_q"), curses.A_DIM)

        if state.last_error:
            safe_addstr(stdscr, y0 + len(fields) + 10, 2, f"{t(lang, 'error')}: {state.last_error}", curses.A_BOLD)

        footer_attr = curses.A_REVERSE if idx == help_idx else 0
        draw_footer(stdscr, t(lang, "termux_footer"), footer_attr)
        stdscr.refresh()

        ch = stdscr.getch()

        if ch in (ord('q'), ord('Q')):
            break
        elif ch == curses.KEY_UP:
            idx = (idx - 1) % (len(fields) + 1)
        elif ch == curses.KEY_DOWN:
            idx = (idx + 1) % (len(fields) + 1)
        elif ch in (ord('c'), ord('C')):
            calc_estimate(state, video_bitrates, audio_bitrates, lang)
        elif ch in (ord('f'), ord('F')):
            selected = pick_video_file(stdscr, state.input_file or os.getcwd(), lang)
            if selected is not None:
                state.input_file = selected
                calc_estimate(state, video_bitrates, audio_bitrates, lang)
        elif ch in (ord('r'), ord('R')):
            calc_estimate(state, video_bitrates, audio_bitrates, lang)
            run_ffmpeg_screen(stdscr, state, video_bitrates, audio_bitrates, lang)
            # after run, recalc (correction factor might change)
            calc_estimate(state, video_bitrates, audio_bitrates, lang)
        elif ch in (curses.KEY_LEFT, curses.KEY_RIGHT) and idx < len(fields):
            direction = -1 if ch == curses.KEY_LEFT else 1
            key = fields[idx][1]
            if key == "scale":
                state.scale_idx = (state.scale_idx + direction) % len(SCALE_OPTIONS)
            elif key == "vbr":
                state.vbr_idx = (state.vbr_idx - direction) % len(video_bitrates)
            elif key == "fr":
                state.fr_idx = (state.fr_idx + direction) % len(FRAMERATES)
            elif key == "ac":
                state.ac_idx = (state.ac_idx + direction) % len(AUDIO_CHANNELS)
            elif key == "abr":
                state.abr_idx = (state.abr_idx - direction) % len(audio_bitrates)
            elif key == "sr":
                state.sr_idx = (state.sr_idx - direction) % len(SAMPLE_RATES)
            calc_estimate(state, video_bitrates, audio_bitrates, lang)

        elif ch in (10, 13, curses.KEY_ENTER):
            if idx == help_idx:
                show_termux_help(stdscr, lang)
                continue

            key = fields[idx][1]
            if key == "input":
                selected = pick_video_file(stdscr, state.input_file or os.getcwd(), lang)
                if selected is not None:
                    state.input_file = selected
                    calc_estimate(state, video_bitrates, audio_bitrates, lang)

            elif key == "scale":
                state.scale_idx = (state.scale_idx + 1) % len(SCALE_OPTIONS)
                calc_estimate(state, video_bitrates, audio_bitrates, lang)

            elif key == "vbr":
                val = edit_int_popup(stdscr, t(lang, "video_bitrate_title"), int(video_bitrates[state.vbr_idx]), lang)
                if val is not None:
                    state.vbr_idx = insert_value_sorted_desc(video_bitrates, int(val))
                    # Persist custom value if it wasn't in base
                    if val not in VIDEO_BITRATES_BASE:
                        custom_v = merge_sorted_desc(custom_v, [val])
                        # Store ascending/descending? store descending
                        save_custom_bitrates(sorted(set(custom_v), reverse=True), sorted(set(custom_a), reverse=True))
                    calc_estimate(state, video_bitrates, audio_bitrates, lang)

            elif key == "abr":
                val = edit_int_popup(stdscr, t(lang, "audio_bitrate_title"), int(audio_bitrates[state.abr_idx]), lang)
                if val is not None:
                    state.abr_idx = insert_value_sorted_desc(audio_bitrates, int(val))
                    if val not in AUDIO_BITRATES_BASE:
                        custom_a = merge_sorted_desc(custom_a, [val])
                        save_custom_bitrates(sorted(set(custom_v), reverse=True), sorted(set(custom_a), reverse=True))
                    calc_estimate(state, video_bitrates, audio_bitrates, lang)


def main():
    curses.wrapper(main_screen)


if __name__ == "__main__":
    main()
