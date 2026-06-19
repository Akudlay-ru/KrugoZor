# Repository audit — 2026-06-19

## Purpose

Compare the repository state with the current working sources and prepare `Akudlay-ru/KrugoZor` for the v15 release candidate.

## Previous repository state

| Element | State |
|---|---|
| Main published code | `KruGoZor_11_5.py` |
| Version in code | `11.5 - 25.08.2025` |
| README | Started `python KruGoZor_11_5.py` |
| CHANGELOG | Stated that v12 was prepared locally but not added |
| Build script | `build_11_5.bat` |
| FaceDirector module | Not present as a separate file |
| External style | Not present as the current root `style.qss` |

## Current working sources

| File | Purpose | Result |
|---|---|---|
| `KruGoZor.pyw` | Main program, `APP_VERSION = 15.0-full-worker — 18.05.2026` | Current main source |
| `kgz_face_director.py` | Isolated face auto-composition module | Required for full dynamic crop functionality |
| `style.qss` | External UI theme | Required for the current visual state |
| `KruGoZor_preview.patch` | Historical preview patch | Keep only in archive |
| `kgz_face_director_preview.patch` | Historical FaceDirector preview patch | Keep only in archive |

## Decision

The repository must use these root files as the current version:

1. `KruGoZor.pyw`
2. `kgz_face_director.py`
3. `style.qss`
4. `README.md`
5. `CHANGELOG.md`
6. `requirements.txt`
7. `requirements-optional.txt`
8. `build.bat`

The old root files `KruGoZor_11_5.py` and `build_11_5.bat` should be removed from the release branch after the v15 files are present.

## Checks

| Check | Result |
|---|---|
| `python3 -m py_compile KruGoZor.pyw kgz_face_director.py` | OK |
| Camera runtime test | Requires Windows and a physical/virtual camera |
| PTZ test | Depends on camera and DirectShow driver |

## Remaining risks

| Risk | Handling |
|---|---|
| `mediapipe` may be unavailable for a Python version | Keep it optional; fallback remains available |
| PTZ may not work for some cameras | Treat PTZ as optional |
| PyInstaller may need local Windows tuning | Verify build on the target PC |
| Old `config.json` may contain legacy fields | The code should normalize loaded config data |
