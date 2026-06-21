# Repository Guidelines

## Project Structure & Module Organization

This repository contains Termux-friendly Python utilities for Android video processing with FFmpeg.

- `ffmpegcompressor.py`: main curses TUI for compressing videos, estimating output size, and saving local bitrate/correction settings.
- `video_rotate.py`: separate curses TUI for rotating videos and optionally forcing a vertical 9:16 output.
- `README.md`: user-facing setup and usage documentation in Spanish.
- `images/`: screenshots used by the README.
- `*.example.json`: documented templates for local generated configuration files.

Runtime files such as `custom_bitrates.json` and `correction_factor.json` are user-specific and should stay untracked.

## Build, Test, and Development Commands

There is no build step. Run the scripts directly from the repository root:

```bash
python ffmpegcompressor.py
python video_rotate.py
```

Required Termux dependencies:

```bash
pkg install python ffmpeg
termux-setup-storage
```

Use `python -m py_compile ffmpegcompressor.py video_rotate.py` for a quick syntax check before committing.

## Coding Style & Naming Conventions

Use Python 3 with standard-library dependencies unless there is a clear reason to add more. Follow the existing style: 4-space indentation, descriptive snake_case function names, uppercase constants, and explicit command argument lists for `subprocess` calls. Prefer `pathlib.Path` for new path-heavy code, but keep surrounding style consistent when editing existing functions.

Keep terminal UI text concise and readable on small mobile screens. Preserve UTF-8 encoding when editing files that contain Spanish text or symbols.

## Testing Guidelines

No automated test suite is currently present. For changes to FFmpeg command construction, add focused tests if introducing a test framework; otherwise verify manually with a short sample video. At minimum, run:

```bash
python -m py_compile ffmpegcompressor.py video_rotate.py
```

When behavior changes, test the relevant TUI path in Termux, including cancel/quit paths and output filename collision handling.

## Commit & Pull Request Guidelines

Recent history uses short imperative messages and occasional Conventional Commit prefixes, for example `docs: ...` and `fix(ffmpeg): ...`. Prefer concise messages such as `fix(ffmpeg): handle missing input file` or `docs: update Termux setup`.

Pull requests should include a brief summary, manual test notes, linked issues when applicable, and screenshots or terminal output for visible TUI/documentation changes.

## Security & Configuration Tips

Never commit personal media files or generated local JSON settings. Keep FFmpeg invocations as argument lists instead of shell strings so filenames with spaces are handled safely.
