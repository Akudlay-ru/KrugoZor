# Repository audit — 2026-06-19

## Purpose

Prepare `Akudlay-ru/KrugoZor` for the current v15 main line.

## Confirmed current source files

| File | Status | Purpose |
|---|---|---|
| `KruGoZor.pyw` | present in `main` | Current main program |
| `kgz_face_director.py` | present in `main` | FaceDirector module |
| `requirements.txt` | present in `main` | Base dependencies |
| `requirements-optional.txt` | present in `main` | Optional MediaPipe dependency |
| `build.bat` | present in `main` | PyInstaller build script |

## Legacy files

| File | Decision |
|---|---|
| `KruGoZor_11_5.py` | Remove from root after `KruGoZor.pyw` is confirmed |
| `build_11_5.bat` | Remove from root after `build.bat` is confirmed |

## Checks

| Check | Result |
|---|---|
| `KruGoZor.pyw` visible in GitHub API | OK |
| `kgz_face_director.py` visible in GitHub API | OK |
| README points to `KruGoZor.pyw` | OK after update |
| CHANGELOG mentions current v15 line | OK after update |

## Remaining runtime checks

| Check | Environment |
|---|---|
| Camera capture | Windows 10/11 with physical camera |
| Virtual camera | Windows with supported `pyvirtualcam` backend |
| PTZ | Camera/driver-dependent |
| PyInstaller build | Local Windows machine |
