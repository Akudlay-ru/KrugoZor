# Changelog

## 15.0-full-worker — repository snapshot 2026-06-19

- Main entry point is now `KruGoZor.pyw`.
- Added `kgz_face_director.py`.
- Added `style.qss`.
- Repository is prepared for the current v15 working line.
- Added release preparation files: `requirements.txt`, `requirements-optional.txt`, `.gitignore`, `build.bat` and repository audit.
- Old root files `KruGoZor_11_5.py` and `build_11_5.bat` are legacy and should not be used as the main version.

## 15.0-full-worker — 18.05.2026

- Camera processing moved to a worker-oriented structure.
- Main GUI timer remains responsible for rendering and UI pipeline.
- Improved shutdown and camera release stability.
- Restored `+`, `=`, `-` hotkeys for window size control.
- Context menu cleaned up: quick actions separated from detailed settings tabs.

## 14.x / 13.x

- Stabilized camera, config, logger and CLI.
- Reworked chroma key settings.
- Reworked soft vignette.
- Updated hotkeys, tray menu and about window.
- Reworked virtual camera output modes.

## 12.0

- Version was prepared locally as `KruGoZor_12.pyw`, but was not published to the repository.

## 11.5

- Last old published version: `KruGoZor_11_5.py`.
- Camera window: circle/square.
- Crop, mirror, opacity, chroma key, tray, virtual camera.
