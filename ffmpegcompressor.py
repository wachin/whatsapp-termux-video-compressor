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


def draw_footer(stdscr, msg: str):
    h, w = stdscr.getmaxyx()
    stdscr.hline(h - 2, 0, curses.ACS_HLINE, w)
    stdscr.addnstr(h - 1, 2, msg, max(0, w - 4))


def edit_text_popup(stdscr, title: str, initial: str) -> Optional[str]:
    h, w = stdscr.getmaxyx()
    ph = 7
    pw = min(max(50, len(initial) + 10), max(20, w - 4))
    y = (h - ph) // 2
    x = (w - pw) // 2
    win = curses.newwin(ph, pw, y, x)
    win.border()
    safe_addstr(win, 0, 2, f" {title} ", curses.A_BOLD)
    safe_addstr(win, 2, 2, "Ruta del archivo (pega o escribe):")

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


def pick_video_file(stdscr, start_path: str) -> Optional[str]:
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
        draw_header(stdscr, "Seleccionar video")
        h, w = stdscr.getmaxyx()
        safe_addstr(stdscr, 2, 2, f"Carpeta: {current_dir}", curses.A_BOLD)
        if last_error:
            safe_addstr(stdscr, 3, 2, f"Error: {last_error}", curses.A_BOLD)

        list_y = 4
        visible = max(1, h - 7)
        if idx < top:
            top = idx
        elif idx >= top + visible:
            top = idx - visible + 1

        if not entries:
            safe_addstr(stdscr, list_y, 2, "(sin carpetas ni videos soportados)")
        else:
            for row, (label, path) in enumerate(entries[top:top + visible]):
                attr = curses.A_REVERSE if top + row == idx else 0
                prefix = "[D] " if os.path.isdir(path) else "[V] "
                safe_addstr(stdscr, list_y + row, 2, prefix + label, attr)

        draw_footer(stdscr, "↑↓ mover | Enter abrir/elegir | q/ESC cancelar")
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


def edit_int_popup(stdscr, title: str, initial: int, min_v: int = 10, max_v: int = 50000) -> Optional[int]:
    h, w = stdscr.getmaxyx()
    ph = 9
    pw = min(60, max(20, w - 4))
    y = (h - ph) // 2
    x = (w - pw) // 2
    win = curses.newwin(ph, pw, y, x)
    win.border()
    safe_addstr(win, 0, 2, f" {title} ", curses.A_BOLD)
    safe_addstr(win, 2, 2, f"Escribe un número ({min_v}–{max_v}) y presiona Enter:")
    safe_addstr(win, 3, 2, "ESC = cancelar")

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


def calc_estimate(state: AppState, video_bitrates: List[int], audio_bitrates: List[int]) -> None:
    state.last_error = ""
    if not state.input_file:
        state.estimated_mb = None
        return
    if not os.path.isfile(state.input_file):
        state.estimated_mb = None
        state.last_error = "Archivo no encontrado."
        return
    try:
        dur = ffprobe_duration_seconds(state.input_file)
        v_kbps = int(video_bitrates[state.vbr_idx])
        a_kbps = int(audio_bitrates[state.abr_idx])
        state.estimated_mb = estimate_size_mb(dur, v_kbps, a_kbps, state.correction_factor)
    except FileNotFoundError:
        state.estimated_mb = None
        state.last_error = "No se encontró ffprobe. En Termux: pkg install ffmpeg"
    except subprocess.CalledProcessError:
        state.estimated_mb = None
        state.last_error = "ffprobe falló. ¿Existe ffprobe/ffmpeg en Termux?"
    except Exception as e:
        state.estimated_mb = None
        state.last_error = f"Error: {e}"


def run_ffmpeg_screen(stdscr, state: AppState, video_bitrates: List[int], audio_bitrates: List[int]) -> None:
    stdscr.clear()
    draw_header(stdscr, "Compresor FFmpeg (curses) — Ejecutando")
    h, w = stdscr.getmaxyx()

    if not state.input_file or not os.path.isfile(state.input_file):
        draw_footer(stdscr, "No hay archivo válido. Presiona cualquier tecla para volver.")
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

    safe_addstr(stdscr, 2, 2, "Comando:", curses.A_BOLD)
    safe_addstr(stdscr, 2, 11, " ".join(shlex.quote(arg) for arg in cmd)[: max(0, w - 12)])
    safe_addstr(stdscr, h - 3, 2, "Teclas: ", curses.A_BOLD)
    safe_addstr(stdscr, h - 3, 10, "s=Stop   q=Volver (si está corriendo, detiene primero)")

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
        draw_footer(stdscr, "No se encontró ffmpeg. En Termux: pkg install ffmpeg")
        stdscr.refresh()
        stdscr.getch()
        return
    except Exception as e:
        draw_footer(stdscr, f"No se pudo ejecutar ffmpeg: {e}")
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
    draw_header(stdscr, "Compresor FFmpeg (curses) — Resultado")

    if stopped:
        safe_addstr(stdscr, 3, 2, "Estado: Proceso detenido por el usuario.", curses.A_BOLD)
    elif rc == 0:
        safe_addstr(stdscr, 3, 2, "Estado: Éxito. Video comprimido guardado.", curses.A_BOLD)
        safe_addstr(stdscr, 5, 2, f"Salida: {output_file}")
        try:
            # Update correction factor (and persist)
            new_factor, new_n = update_correction_with_result(state.estimated_mb, state.correction_factor, state.correction_n, output_file)
            state.correction_factor, state.correction_n = new_factor, new_n
            save_correction_factor(state.correction_factor, state.correction_n)
            safe_addstr(stdscr, 7, 2, f"Factor de corrección actualizado: {state.correction_factor:.4f} (n={state.correction_n})")
            safe_addstr(stdscr, 8, 2, f"Tamaño real: {get_file_size_mb(output_file):.2f} MB")
        except Exception as e:
            safe_addstr(stdscr, 7, 2, f"No se pudo actualizar el factor: {e}")
    else:
        safe_addstr(stdscr, 3, 2, f"Estado: Falló (código {rc}).", curses.A_BOLD)
        safe_addstr(stdscr, 5, 2, "Revisa la salida anterior (ffmpeg).")

    draw_footer(stdscr, "Presiona cualquier tecla para volver al menú.")
    stdscr.refresh()
    stdscr.getch()


def main_screen(stdscr) -> None:
    curses.curs_set(0)
    curses.use_default_colors()
    stdscr.keypad(True)

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

    calc_estimate(state, video_bitrates, audio_bitrates)

    fields = [
        ("Archivo de entrada", "input"),
        ("Escala", "scale"),
        ("Bitrate video (k)", "vbr"),
        ("Framerate", "fr"),
        ("Canales audio", "ac"),
        ("Bitrate audio (k)", "abr"),
        ("Sample rate", "sr"),
    ]
    idx = 0

    while True:
        stdscr.erase()
        draw_header(stdscr, "Compresor de Video FFmpeg — Termux (curses)")

        h, w = stdscr.getmaxyx()
        safe_addstr(stdscr, 2, 2, "↑↓ mover | ←→ cambiar | Enter editar | f buscar video | c calcular | r comprimir | q salir", curses.A_DIM)

        y0 = 4
        for i, (label, key) in enumerate(fields):
            attr = curses.A_REVERSE if i == idx else 0
            safe_addstr(stdscr, y0 + i, 2, f"{label:16}:", (attr | curses.A_BOLD) if i == idx else curses.A_BOLD)

            if key == "input":
                val = state.input_file or "(vacío)"
            elif key == "scale":
                val = SCALE_OPTIONS[state.scale_idx]
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

        est_line = "Tamaño estimado: N/A"
        if state.estimated_mb is not None:
            est_line = f"Tamaño estimado: {state.estimated_mb:.2f} MB"
        safe_addstr(stdscr, y0 + len(fields) + 1, 2, est_line, curses.A_BOLD)

        safe_addstr(stdscr, y0 + len(fields) + 3, 2, f"Factor de corrección: {state.correction_factor:.4f} (n={state.correction_n})")
        safe_addstr(stdscr, y0 + len(fields) + 4, 2, f"Bitrates manuales guardados en: {CUSTOM_BITRATES_FILE}", curses.A_DIM)

        if state.last_error:
            safe_addstr(stdscr, y0 + len(fields) + 6, 2, f"Error: {state.last_error}", curses.A_BOLD)

        draw_footer(stdscr, "Tip Termux: termux-setup-storage para /storage/emulated/0/ ...")
        stdscr.refresh()

        ch = stdscr.getch()

        if ch in (ord('q'), ord('Q')):
            break
        elif ch == curses.KEY_UP:
            idx = (idx - 1) % len(fields)
        elif ch == curses.KEY_DOWN:
            idx = (idx + 1) % len(fields)
        elif ch in (ord('c'), ord('C')):
            calc_estimate(state, video_bitrates, audio_bitrates)
        elif ch in (ord('f'), ord('F')):
            selected = pick_video_file(stdscr, state.input_file or os.getcwd())
            if selected is not None:
                state.input_file = selected
                calc_estimate(state, video_bitrates, audio_bitrates)
        elif ch in (ord('r'), ord('R')):
            calc_estimate(state, video_bitrates, audio_bitrates)
            run_ffmpeg_screen(stdscr, state, video_bitrates, audio_bitrates)
            # after run, recalc (correction factor might change)
            calc_estimate(state, video_bitrates, audio_bitrates)
        elif ch in (curses.KEY_LEFT, curses.KEY_RIGHT):
            direction = -1 if ch == curses.KEY_LEFT else 1
            key = fields[idx][1]
            if key == "scale":
                state.scale_idx = (state.scale_idx + direction) % len(SCALE_OPTIONS)
            elif key == "vbr":
                state.vbr_idx = (state.vbr_idx + direction) % len(video_bitrates)
            elif key == "fr":
                state.fr_idx = (state.fr_idx + direction) % len(FRAMERATES)
            elif key == "ac":
                state.ac_idx = (state.ac_idx + direction) % len(AUDIO_CHANNELS)
            elif key == "abr":
                state.abr_idx = (state.abr_idx + direction) % len(audio_bitrates)
            elif key == "sr":
                state.sr_idx = (state.sr_idx + direction) % len(SAMPLE_RATES)
            calc_estimate(state, video_bitrates, audio_bitrates)

        elif ch in (10, 13, curses.KEY_ENTER):
            key = fields[idx][1]
            if key == "input":
                edited = edit_text_popup(stdscr, "Archivo de entrada", state.input_file)
                if edited is not None:
                    state.input_file = edited
                    calc_estimate(state, video_bitrates, audio_bitrates)

            elif key == "vbr":
                val = edit_int_popup(stdscr, "Bitrate de video (kbit/s)", int(video_bitrates[state.vbr_idx]))
                if val is not None:
                    state.vbr_idx = insert_value_sorted_desc(video_bitrates, int(val))
                    # Persist custom value if it wasn't in base
                    if val not in VIDEO_BITRATES_BASE:
                        custom_v = merge_sorted_desc(custom_v, [val])
                        # Store ascending/descending? store descending
                        save_custom_bitrates(sorted(set(custom_v), reverse=True), sorted(set(custom_a), reverse=True))
                    calc_estimate(state, video_bitrates, audio_bitrates)

            elif key == "abr":
                val = edit_int_popup(stdscr, "Bitrate de audio (kbit/s)", int(audio_bitrates[state.abr_idx]))
                if val is not None:
                    state.abr_idx = insert_value_sorted_desc(audio_bitrates, int(val))
                    if val not in AUDIO_BITRATES_BASE:
                        custom_a = merge_sorted_desc(custom_a, [val])
                        save_custom_bitrates(sorted(set(custom_v), reverse=True), sorted(set(custom_a), reverse=True))
                    calc_estimate(state, video_bitrates, audio_bitrates)


def main():
    curses.wrapper(main_screen)


if __name__ == "__main__":
    main()
