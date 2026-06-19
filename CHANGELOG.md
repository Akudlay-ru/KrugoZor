# Changelog

## Current v15 main snapshot — 2026-06-20

- Main entry point is now `KruGoZor.pyw`.
- Added `kgz_face_director.py` as the separate FaceDirector module.
- Repository documentation and build flow are aligned with the current v15 working line.
- Old root files from the 11.5 line are no longer the release entry point.

## v15 working line

- Camera processing moved to a worker-oriented structure.
- Main GUI timer remains responsible for rendering and UI pipeline.
- Improved shutdown and camera release stability.
- Restored `+`, `=`, `-` hotkeys for window size control.
- Context menu cleaned up: quick actions separated from detailed settings tabs.
- Dynamic crop and FaceDirector support are kept in the current source set.

## 14.x / 13.x

- Stabilized camera, config, logger and CLI.
- Reworked chroma key settings.
- Reworked soft vignette.
- Updated hotkeys, tray menu and about window.
- Reworked virtual camera output modes.

## 12.0

- Version was prepared locally as `KruGoZor_12.pyw`, but was not published as the main repository source at that stage.

## 11.5

- Last old published version: `KruGoZor_11_5.py`.
- Camera window: circle/square.
- Crop, mirror, opacity, chroma key, tray, virtual camera.
