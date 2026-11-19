from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs

root = Path(SPECPATH)
analysis = Analysis(
    [str(root / "KruGoZor.pyw")],
    pathex=[str(root)],
    binaries=collect_dynamic_libs("mediapipe"),
    datas=[(str(root / name), ".") for name in (
        "style.qss", "face_landmarker.task", "selfie_segmenter.tflite",
    )],
    hiddenimports=["PyQt5.sip", "mediapipe.tasks.c"],
    excludes=["pandas", "openpyxl", "lxml", "sounddevice", "tkinter", "PIL._avif"],
)
# Local cameras use DirectShow on Windows. OpenCV's separate FFmpeg plugin
# is only needed for its FFmpeg video I/O backend.
analysis.binaries = [
    entry for entry in analysis.binaries
    if not Path(entry[0]).name.lower().startswith("opencv_videoio_ffmpeg")
]
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, analysis.binaries, analysis.datas, [],
    name="KruGoZor-lite",
    console=False,
    icon=str(root / "icon.ico"),
)
