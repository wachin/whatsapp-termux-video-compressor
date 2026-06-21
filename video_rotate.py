#!/usr/bin/env python3
import curses
import os
import shlex
import subprocess
from pathlib import Path

APP_TITLE = "Termux Video Rotator (ffmpeg + curses) — vertical 9:16 opcional"

ROTATE_OPTIONS = [
    ("No rotar", None),
    ("90° a la derecha (clockwise)", "cw"),
    ("90° a la izquierda (counterclockwise)", "ccw"),
    ("180°", "180"),
]

FILL_OPTIONS = [
    ("No (solo rotar, mantén tamaño original)", False),
    ("Sí (forzar vertical 9:16 con zoom + recorte centrado)", True),
]

def run_cmd(cmd):
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        return None

def ffprobe_wh(path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height", "-of", "csv=p=0", path]
    p = run_cmd(cmd)
    if p is None:
        return None, None, "No se encontró ffprobe. En Termux: pkg install ffmpeg"
    if p.returncode != 0 or not p.stdout.strip():
        return None, None, p.stderr.strip()
    try:
        w, h = p.stdout.strip().split(",")
        return int(w), int(h), ""
    except Exception:
        return None, None, "No pude parsear width/height."

def build_filter(rotate_mode, fill_916, in_w, in_h):
    # Rotación: usamos transpose/rotate clásico (rápido y compatible)
    vf_parts = []

    if rotate_mode == "cw":
        vf_parts.append("transpose=1")  # clockwise
    elif rotate_mode == "ccw":
        vf_parts.append("transpose=2")  # counterclockwise
    elif rotate_mode == "180":
        vf_parts.append("hflip,vflip")

    # Si el usuario quiere 9:16 (vertical), hacemos:
    # 1) Escalar para cubrir el área 1080x1920 manteniendo aspecto
    # 2) Recortar centrado
    # Puedes cambiar 1080x1920 por 720x1280 si quieres más liviano.
    if fill_916:
        target_w, target_h = 1080, 1920
        # scale con force_original_aspect_ratio=increase cubre el lienzo
        vf_parts.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase")
        vf_parts.append(f"crop={target_w}:{target_h}")
        # además fijamos SAR 1:1 para evitar “estiramientos raros”
        vf_parts.append("setsar=1")

    return ",".join(vf_parts)

def ensure_out_path(in_path, suffix):
    p = Path(in_path)
    out = p.with_name(p.stem + suffix + p.suffix)
    # evitar sobreescritura
    i = 1
    while out.exists():
        out = p.with_name(p.stem + f"{suffix}_{i}" + p.suffix)
        i += 1
    return str(out)

def draw_menu(stdscr, title, items, idx, footer="↑/↓ mover  Enter elegir  q salir"):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(0, 0, title[:w-1], curses.A_BOLD)
    stdscr.addstr(1, 0, "-" * min(w-1, 80))
    y = 3
    for i, it in enumerate(items):
        text = it
        if i == idx:
            stdscr.addstr(y+i, 2, f"> {text}"[:w-4], curses.A_REVERSE)
        else:
            stdscr.addstr(y+i, 2, f"  {text}"[:w-4])
    stdscr.addstr(h-2, 0, footer[:w-1], curses.A_DIM)
    stdscr.refresh()

def prompt_input(stdscr, prompt, default=""):
    curses.echo()
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(0, 0, APP_TITLE[:w-1], curses.A_BOLD)
    stdscr.addstr(2, 0, prompt[:w-1])
    stdscr.addstr(4, 0, f"Default: {default}"[:w-1], curses.A_DIM)
    stdscr.addstr(6, 0, "> ")
    stdscr.refresh()
    s = stdscr.getstr(6, 2, 4096).decode("utf-8").strip()
    curses.noecho()
    if not s:
        return default
    return s

def pick_option(stdscr, title, options):
    idx = 0
    labels = [o[0] for o in options]
    while True:
        draw_menu(stdscr, title, labels, idx)
        k = stdscr.getch()
        if k in (curses.KEY_UP, ord('k')):
            idx = (idx - 1) % len(labels)
        elif k in (curses.KEY_DOWN, ord('j')):
            idx = (idx + 1) % len(labels)
        elif k in (curses.KEY_ENTER, 10, 13):
            return options[idx]
        elif k in (ord('q'), 27):
            return None

def show_log(stdscr, title, lines):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(0, 0, title[:w-1], curses.A_BOLD)
    stdscr.addstr(1, 0, "-" * min(w-1, 80))
    y = 3
    for ln in lines[-(h-6):]:
        stdscr.addstr(y, 0, ln[:w-1])
        y += 1
        if y >= h-3:
            break
    stdscr.addstr(h-2, 0, "Presiona cualquier tecla para salir..."[:w-1], curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)

    # 1) Ruta del video
    default_path = str(Path.home())
    in_path = prompt_input(
        stdscr,
        "Ruta del video (puedes pegarla). Tip: en Termux suele estar en /sdcard/...",
        default=default_path
    )

    if os.path.isdir(in_path):
        # si dio una carpeta, pedimos el archivo
        in_path = prompt_input(stdscr, "Esa ruta es una carpeta. Pega la ruta completa del archivo de video:", default="")

    in_path = os.path.expanduser(in_path)

    if not os.path.exists(in_path):
        show_log(stdscr, "Error", [f"No existe: {in_path}"])
        return

    # 2) Rotación
    rot = pick_option(stdscr, "Elige rotación", ROTATE_OPTIONS)
    if rot is None:
        return
    rot_label, rot_mode = rot

    # 3) Forzar vertical 9:16
    fill = pick_option(stdscr, "¿Forzar formato vertical 9:16?", FILL_OPTIONS)
    if fill is None:
        return
    fill_label, fill_916 = fill

    # 4) ffprobe dimensiones
    w, h, err = ffprobe_wh(in_path)
    if w is None:
        show_log(stdscr, "Error ffprobe", [err or "No pude leer dimensiones del video."])
        return

    vf = build_filter(rot_mode, fill_916, w, h)
    out_path = ensure_out_path(in_path, suffix="_VERTICAL" if fill_916 else "_ROTATED")

    # 5) Comando ffmpeg
    cmd = ["ffmpeg", "-y", "-i", in_path]

    if vf:
        cmd += ["-vf", vf]

    # Encode: H.264 + AAC (compatible)
    # CRF 23 buen equilibrio; baja a 20 si quieres más calidad, sube a 26 si quieres más liviano
    cmd += ["-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k", out_path]

    # 6) Ejecutar y mostrar salida en pantalla
    stdscr.clear()
    hh, ww = stdscr.getmaxyx()
    stdscr.addstr(0, 0, APP_TITLE[:ww-1], curses.A_BOLD)
    stdscr.addstr(2, 0, f"Entrada : {in_path}"[:ww-1])
    stdscr.addstr(3, 0, f"Rotación: {rot_label}"[:ww-1])
    stdscr.addstr(4, 0, f"9:16    : {fill_label}"[:ww-1])
    stdscr.addstr(5, 0, f"Salida  : {out_path}"[:ww-1])
    stdscr.addstr(7, 0, "Ejecutando ffmpeg... (puede demorar)"[:ww-1], curses.A_DIM)
    stdscr.addstr(9, 0, "Comando:"[:ww-1], curses.A_BOLD)
    stdscr.addstr(10, 0, " ".join(shlex.quote(x) for x in cmd)[:ww-1], curses.A_DIM)
    stdscr.refresh()

    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        show_log(stdscr, "❌ Error", ["No se encontró ffmpeg. En Termux: pkg install ffmpeg"])
        return
    _, stderr = p.communicate()

    lines = stderr.splitlines()

    if p.returncode == 0 and os.path.exists(out_path):
        show_log(stdscr, "✅ Listo", [
            "Procesado con éxito.",
            f"Archivo generado: {out_path}",
            "",
            "Tip: si tu proyecto está en /sdcard, ya lo puedes cargar en VN."
        ])
    else:
        show_log(stdscr, "❌ Error", lines[-200:] if lines else ["ffmpeg falló sin salida."])

if __name__ == "__main__":
    curses.wrapper(main)
