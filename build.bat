@echo off
setlocal ENABLEDELAYEDEXPANSION
chcp 65001 >nul

set "PYTHON=py"
set "SCRIPT=KruGoZor.pyw"
set "APPNAME=KruGoZor"
set "ICON=icon.ico"

if not exist "%SCRIPT%" (
  echo [ERROR] %SCRIPT% not found.
  pause
  exit /b 1
)

echo ============= KrugoZor build =============
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install --upgrade pyinstaller
%PYTHON% -m pip install -r requirements.txt

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q "%APPNAME%.spec" 2>nul

set "ICON_ARG="
if exist "%ICON%" set "ICON_ARG=--icon %ICON%"

%PYTHON% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name "%APPNAME%" ^
  %ICON_ARG% ^
  --hidden-import PyQt5.sip ^
  --collect-submodules keyboard ^
  --collect-submodules psutil ^
  --collect-submodules pyvirtualcam ^
  --collect-submodules cv2 ^
  --add-data "style.qss;." ^
  "%SCRIPT%"

if exist dist (
  if exist "style.qss" copy /y "style.qss" "dist\style.qss" >nul
  if exist "%ICON%" copy /y "%ICON%" "dist\%ICON%" >nul
)

echo.
echo [OK] Build finished: dist\%APPNAME%.exe
pause
