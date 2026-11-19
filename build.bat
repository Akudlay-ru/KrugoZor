@echo off
setlocal
pushd "%~dp0" || exit /b 1

set "PYTHON=py"
set "SCRIPT=KruGoZor.pyw"
set "APPNAME=KruGoZor"
set "ICON=icon.ico"

if /i "%~1"=="launcher" (
  if not exist "dist" mkdir "dist"
  "%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:winexe ^
    /platform:anycpu /optimize+ /codepage:65001 /win32icon:icon.ico ^
    /reference:System.Windows.Forms.dll /reference:System.Drawing.dll ^
    /out:"dist\KruGoZor-lite-launcher.exe" "LiteLauncher.cs" || goto :failed
  echo [OK] Build finished: dist\KruGoZor-lite-launcher.exe
  popd
  exit /b 0
)

for %%F in ("%SCRIPT%" "%ICON%" "style.qss" "face_landmarker.task" "selfie_segmenter.tflite") do (
  if not exist "%%~F" (
    echo [ERROR] Missing file: %%~F
    goto :failed
  )
)

%PYTHON% -c "import PyInstaller, mediapipe" || (
  echo [ERROR] PyInstaller and MediaPipe are required in the build interpreter.
  goto :failed
)

if /i "%~1"=="lite" (
  %PYTHON% -m PyInstaller --noconfirm "KruGoZor-lite.spec" || goto :failed
  if not exist "dist\KruGoZor-lite.exe" goto :failed
  echo [OK] Build finished: dist\KruGoZor-lite.exe
  popd
  exit /b 0
)

%PYTHON% -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "%APPNAME%" ^
  --icon "%ICON%" ^
  --hidden-import PyQt5.sip ^
  --collect-submodules keyboard ^
  --collect-submodules psutil ^
  --collect-submodules pyvirtualcam ^
  --collect-submodules cv2 ^
  --collect-all mediapipe ^
  --add-data "style.qss;." ^
  --add-data "face_landmarker.task;." ^
  --add-data "selfie_segmenter.tflite;." ^
  "%SCRIPT%" || goto :failed

if not exist "dist\%APPNAME%.exe" goto :failed
echo [OK] Build finished: dist\%APPNAME%.exe
popd
exit /b 0

:failed
echo [ERROR] Build failed.
popd
exit /b 1
