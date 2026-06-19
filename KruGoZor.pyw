#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
КругоЗор — минималистичная «пузырь-камера» поверх всех окон
+ независимая виртуальная камера

v15-menu-mix — чистое контекстное меню и возврат +/- к размеру окна:
  • Горячие клавиши +/=/- снова управляют размером главного окна, а не параметром dynamic circle/head.
  • Контекстное меню собрано заново: возвращены старые рабочие пункты окна, хромакея и виртуальной камеры, но убраны громоздкие ползунки динамического кропа.
  • Настройки остаются во вкладках «Свойства…», а контекстное меню используется для быстрых действий.

v14-full-worker — полный стабилизационный контур с выносом захвата камеры из GUI-потока:
  • Захват кадров перенесён в отдельный Python-worker thread; GUI больше не блокируется на cap.read().
  • Основной QTimer оставлен как рендер/пайплайн КругоЗора: это сохраняет текущую архитектуру окна, vcam, хромакея, PTZ и динамического кропа.
  • PTZ-команды защищены общим lock с worker-захватом, чтобы cap.read() и cap.set()/get() не дрались за один DirectShow handle.
  • Переключение/выключение камеры теперь останавливает worker и освобождает VideoCapture идемпотентно.

v13-stabilized — стабилизационная правка без изменения видеоконтура:
  • Убран зашитый локальный путь разработчика из vcam_bg_path.
  • Исправлены утечки VideoCapture при поиске/проверке камер.
  • Добавлена санитарная проверка config.json после загрузки.
  • Сохранение config.json стало отложенным и атомарным.
  • Logger переинициализируется без дублирования handlers.
  • CLI-параметры проверяются по диапазонам.

v12-ptz-properties-fix — предыдущая рабочая правка:
  • Настройки переведены на вкладки: Хромакей/Виньетка, Кроп, Виртуальная камера, PTZ.
  • Динамический кроп теперь используется и в предпросмотре виньетки окна.
  • PTZ-контур усилен: накопительные абсолютные команды, физические тест-кнопки и более заметные шаги Pan/Tilt.
  • В PTZ-вкладку добавлены ползунки физического положения Pan/Tilt/Zoom с абсолютной отправкой команд.
  • Исправлен вылет при открытии окна свойств/настроек из-за неверного имени метода PTZ-подписей.
  • Динамический кроп ускорен: ROI-поиск вокруг предыдущего лица + без sleep_until_next_frame в QTimer.
  • Режим Телемост использует текущий динамический crop_rect для новой виньетки.
  • PTZ-кнопки Pan/Tilt при динамическом кропе двигают цель, иначе физически двигают камеру.
  • Добавлены запоминание базового положения PTZ/цели и возврат клавишей 0.

v12.0 — глубокая переработка:
  • Убрано дублирование ползунков (opacity/feather) — один обработчик,
    оба меню синхронизируются автоматически
  • Вынесен _open_camera() — единая точка открытия камеры вместо
    трёх копий одного и того же кода
  • Кэш круглой маски — пересчёт только при изменении размера/feather
  • Исправлен баг switch_camera: при ошибке откат на старый индекс
  • Убран monkey-patching _apply_dark_menu_style
  • Действия камеры (QAction) переиспользуются в обоих меню
  • Упрощён build_alpha_mask (лишние промежуточные приведения типов)
  • on_tick: убрана двойная копия кадра, log_cap_props убран из горячего пути
  • contextMenuEvent очищен от ручной синхронизации состояний
  • force_quit/closeEvent — однократная очистка ресурсов
  • Убраны мёртвые методы: apply_menu_opacity, ensure_first_run_files,
    app_exe_dir, _is_frozen
  • import time убран (не использовался)

v13.5 — переписанный модуль хромакея:
  • Хромакей переписан с нуля как изолированный блок кода.
    Модель данных: вместо плоских pickA/B/tolA/B используется
    список из 4 слотов (PickSlot). Слоты A и B включены по
    умолчанию, C и D — выключены, у всех есть чекбокс.
  • Совместимость: при загрузке старых config.json со схемой
    pickA/B/tolA/B значения мигрируют в новую структуру.
  • HSV доработан:
      – ползунки min/max связаны (нижний толкает верхний только
        когда упирается, и наоборот)
      – чекбокс «Кольцевой диапазон H» допускает h_min > h_max
        (для красного цвета, который лежит по обе стороны 0)
      – HSV-маска складывается с масками пипеток через ИЛИ —
        работают одновременно, если включить чекбокс HSV
      – кнопка «Заполнить HSV из пипетки» — берёт цвет из любого
        включённого слота и расставляет диапазоны вокруг
  • Превью в диалоге — переключатель «Оригинал / Результат / Маска»:
      – «Оригинал» — кадр + точки пипеток (как было)
      – «Результат» — кеинг применён, под прозрачностью шахматка
      – «Маска» — чёрно-белая альфа-маска (для отладки порогов)
  • Кнопка «Применить» заменена на «Сбросить настройки хромакея»
    (она теперь делает осмысленную работу).
  • Виньетка переписана аналитически: вместо «бинарная маска +
    cv2.GaussianBlur» используется формула smoothstep по расстоянию
    от центра. Это даёт идеально симметричный мягкий край (нижний
    такой же, как верхний), без зависимости от паддинга гаусса.
    Радиус круга ровно size/2 — окно не «сжимается» с feather.

v13.6 — единая мягкость, hotkeys, пересборка меню:
  • Один ползунок «Мягкость края» вместо двух — управляет
    виньеткой и кеингом синхронно, чтобы переходы выглядели как
    одна общая мягкость. edge_feather из state и feather у chroma
    остаются в модели (для обратной совместимости), но связаны.
  • Допуск каждого слота пипетки — пара слайдер+спин (как HSV).
  • Новый диалог «Hotkeys…» с редактируемыми клавишами через
    QKeySequenceEdit. Привязки создаются динамически из config,
    конфликтные сочетания подсвечиваются и не сохраняются.
  • «О программе» переделано в стиле NumLockCalc: единое тёмное
    полотно с подзаголовками, без иконки 64×64 и группбоксов.
    Ссылки: автор @AKudlay_ru, канал @RoundCam.
  • Контекстное меню перестроено:
      – Подменю «Окно» (Включить, Всегда поверх, Отразить,
        Игнорировать мышь, Круг/Квадрат как радиокнопки).
      – Хромакей/Кроп/Виртуальная камера — пункты, ведущие
        прямо в свои диалоги. Чекбоксы «Включена» переехали
        внутрь этих диалогов.
      – Сброс / Непрозрачность / Hotkeys / О программе / Закрыть.
  • Меню трея идентично контекстному (плюс «Показать окно»).

v13.8 — переработка виртуальной камеры (текущая публичная):
  • Виртуальная камера теперь по умолчанию использует разрешение
    физического источника (не насильно 1280×720). Никаких чёрных
    полос и обрезок при стандартных пропорциях. Аргумент
    --vcam-res остался как override.
  • Чекбокс «По ширине окна» убран из диалога — вместо него
    ползунок «Масштаб» (50–200%): крупнее/мельче лицо в кадре.
  • Кнопка «Обновить список камер» в подменю «Камера» —
    пересканирует доступные устройства без перезапуска. Полезно,
    если включить OBS Virtual Camera уже после старта программы.
  • Новый режим «Лицо в круг» — имитирует круглую аватарку
    видео-сервиса (Я.Телемост и т.п.):
      – загружается фон-картинка через «Загрузить фон…»
      – на ней автоматически детектируется белый круг
        (cv2.HoughCircles) — это то место, куда будет вписано
        живое лицо
      – позицию и радиус круга можно поправить вручную
      – камера с кеингом маскируется этим круглым окном и
        накладывается ровно в центр обнаруженного круга
  • Альтернативный режим «Простая подкладка» — фон просто
    подставляется под прозрачные области кеинга, без круга.
  • Превью результата прямо в диалоге vcam — без него
    настраивать «лицо в круг» было бы пыткой.
  • Загруженный фон хранится только как путь в config
    (без копирования файла — пользователь сам отвечает за него).
  • Добавлены настройки фона для телемоста
"""

from __future__ import annotations

import argparse
import atexit
import base64
import ctypes
import json
import logging
import logging.handlers
import os
import re
import sys
import subprocess
import tempfile
import threading
import time
import traceback
from pathlib import Path
from dataclasses import dataclass, asdict, field
from math import ceil, hypot

os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"
import cv2
import numpy as np

try:
    from kgz_face_director import FaceAutoDirector, FaceDirectorConfig
    HAVE_FACE_DIRECTOR = True
except Exception:
    FaceAutoDirector = None
    FaceDirectorConfig = None
    HAVE_FACE_DIRECTOR = False

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPainter, QRegion, QIcon, QPixmap, QCloseEvent
from PyQt5.QtWidgets import (
    QWidget, QApplication, QMenu, QAction, QDialog, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSlider, QSpinBox, QCheckBox,
    QGroupBox, QSystemTrayIcon, QWidgetAction, QMessageBox, QShortcut,
    QActionGroup, QFileDialog, QColorDialog,
)

try:
    from PyQt5.QtSvg import QSvgRenderer
    HAVE_QTSVG = True
except Exception:
    QSvgRenderer = None
    HAVE_QTSVG = False

try:
    import pyvirtualcam
    HAVE_PYVIRTUALCAM = True
except Exception:
    HAVE_PYVIRTUALCAM = False

# ---------------------------------------------------------------------------
# Встроенная иконка
# ---------------------------------------------------------------------------
def _load_embedded_icon() -> QIcon:
    """Загружает встроенную иконку из base64 (_ICON_B64 определён в конце
    файла). В .ico несколько размеров (16, 32, 48, 64, 128, 256) — добавляем
    в QIcon все, чтобы Qt сам выбирал подходящий для трея/заголовка/диалогов.
    Возвращает пустой QIcon при ошибке."""
    try:
        data = base64.b64decode(_ICON_B64)
        ba = QtCore.QByteArray(data)
        buf = QtCore.QBuffer(ba)
        buf.open(QtCore.QIODevice.ReadOnly)
        reader = QtGui.QImageReader(buf, b"ICO")
        icon = QIcon()
        while True:
            img = reader.read()
            if img.isNull():
                break
            icon.addPixmap(QPixmap.fromImage(img))
            if not reader.jumpToNextImage():
                break
        return icon if not icon.isNull() else QIcon()
    except Exception:
        return QIcon()

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------
APP_NAME    = "КругоЗор"
APP_VERSION = "15.0-full-worker — 18.05.2026"
CONTACT     = "Андрей Кудлай, телеграм: @akudlay_ru"

# ---------------------------------------------------------------------------
# Защита от повторного запуска
# ---------------------------------------------------------------------------
_INSTANCE_MUTEX = None

def _release_instance_mutex():
    """Освобождает Windows mutex при штатном выходе."""
    global _INSTANCE_MUTEX
    if os.name == "nt" and _INSTANCE_MUTEX:
        try:
            ctypes.windll.kernel32.ReleaseMutex(_INSTANCE_MUTEX)
        except Exception:
            pass
        try:
            ctypes.windll.kernel32.CloseHandle(_INSTANCE_MUTEX)
        except Exception:
            pass
    _INSTANCE_MUTEX = None

def _ensure_single_instance() -> bool:
    """Не даёт открыть второй экземпляр, пока первый процесс ещё жив."""
    global _INSTANCE_MUTEX
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        _INSTANCE_MUTEX = kernel32.CreateMutexW(
            None, True, "Local\\KruGoZor_RoundCam_SingleInstance")
        if not _INSTANCE_MUTEX:
            return True
        ERROR_ALREADY_EXISTS = 183
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            user32.MessageBoxW(
                0,
                "КругоЗор уже запущен.\n\n"
                "Если окна не видно, проверьте значок в трее. "
                "Если старый процесс завис, завершите python.exe/pythonw.exe "
                "в Диспетчере задач и запустите программу снова.",
                APP_NAME,
                0x40,
            )
            try:
                kernel32.CloseHandle(_INSTANCE_MUTEX)
            except Exception:
                pass
            _INSTANCE_MUTEX = None
            return False
    except Exception:
        return True
    return True

atexit.register(_release_instance_mutex)

# ---------------------------------------------------------------------------
# Пути и логирование
# ---------------------------------------------------------------------------
def _app_dir() -> str:
    """Папка, в которой лежит скрипт или собранный .exe."""
    if getattr(sys, "frozen", False):
        # Запущено из PyInstaller/Nuitka — берём директорию exe
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def _data_dir() -> str:
    """Портабельная папка данных рядом со скриптом/exe.
    %APPDATA% не используется намеренно — программа должна работать
    как «портабельная»: всё своё носит с собой.
    Если писать в эту директорию нельзя (например, программа
    положена в Program Files без прав), показываем сообщение
    и завершаемся — без молчаливого фолбэка."""
    base = os.path.join(_app_dir(), "KrugoZor_data")
    try:
        for sub in ("", "Logs", "Snapshots"):
            os.makedirs(os.path.join(base, sub), exist_ok=True)
        # Проверка записи
        probe = os.path.join(base, ".write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
    except Exception as e:
        # На этом этапе QApplication ещё нет — используем ctypes MessageBox
        msg = (f"Не могу создать или записать в папку:\n{base}\n\n"
               f"{e}\n\n"
               f"Перенесите программу в каталог с правами на запись "
               f"(например, в свою папку пользователя).")
        try:
            if os.name == "nt":
                ctypes.windll.user32.MessageBoxW(0, msg, APP_NAME, 0x10)
            else:
                sys.stderr.write(msg + "\n")
        except Exception:
            sys.stderr.write(msg + "\n")
        sys.exit(1)
    return base

DATA_DIR    = _data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
LOG_FILE    = os.path.join(DATA_DIR, "Logs", "krugozor.log")
STYLE_FILE  = os.path.join(_app_dir(), "style.qss")

_logger = None

def setup_logger(debug: bool = False) -> logging.Logger:
    """Инициализирует логгер без накопления дублей handler-ов.

    При повторном вызове старые handler-ы закрываются. Иначе после
    перезапуска/тестов одна запись начинает появляться в логе по 2-3 раза,
    что выглядит как мистика, но это просто Python не читает мысли.
    """
    global _logger
    logger = logging.getLogger("KrugoZor")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    if debug:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    logger.info("=== %s %s старт ===", APP_NAME, APP_VERSION)
    logger.info("Python %s | OpenCV %s | Qt %s",
                sys.version.split()[0], cv2.__version__, QtCore.QT_VERSION_STR)
    _logger = logger
    return logger

def _log_exc(msg: str, exc: BaseException):
    if _logger:
        _logger.error("%s: %s\n%s", msg, exc,
                      "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))

def _log_cap(cap: cv2.VideoCapture):
    """Логирует свойства камеры — вызывать только при инициализации/переключении."""
    if not _logger or cap is None:
        return
    try:
        _logger.info("CAP: %.0fx%.0f @%.0ffps",
                     cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                     cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                     cap.get(cv2.CAP_PROP_FPS))
    except Exception:
        pass

def _clamp_int(value, default: int, lo: int, hi: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return int(default)
    return max(int(lo), min(int(hi), value))

def _clamp_float(value, default: float, lo: float, hi: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not np.isfinite(value):
        return float(default)
    return max(float(lo), min(float(hi), value))

def _as_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes", "y", "да", "on"):
            return True
        if v in ("0", "false", "no", "n", "нет", "off"):
            return False
    return bool(default)

def _safe_hex_color(value: object, default: str) -> str:
    if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value.strip()):
        return value.strip()
    return default

def _safe_rect(value, default_rect=None):
    if default_rect is None:
        default_rect = [70, 33, 514, 437]
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return list(default_rect)
    try:
        x, y, w, h = [int(round(float(v))) for v in value]
    except (TypeError, ValueError):
        return list(default_rect)
    w = max(1, w)
    h = max(1, h)
    return [x, y, w, h]

def _safe_pick_color(value):
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    try:
        return [_clamp_int(v, 0, 0, 255) for v in value]
    except Exception:
        return None

def _safe_point(value):
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        return [int(round(float(value[0]))), int(round(float(value[1])))]
    except (TypeError, ValueError):
        return None

def _can_open_camera(index: int, backend: int) -> bool:
    """Проверяет камеру и всегда освобождает VideoCapture."""
    cap = cv2.VideoCapture(int(index), backend)
    try:
        return bool(cap is not None and cap.isOpened())
    finally:
        try:
            cap.release()
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Поиск камер
# ---------------------------------------------------------------------------
def find_cameras(max_search: int = 10,
                 skip_index: int = -1) -> list:
    """Ищет доступные камеры без утечек VideoCapture.

    skip_index — уже открытая камера: добавляем её в список без повторного
    открытия, чтобы не мигать индикатором и не ссориться с драйвером.
    """
    backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
    indices = []
    for i in range(max_search):
        if i == skip_index:
            indices.append(i)
            continue
        if _can_open_camera(i, backend):
            indices.append(i)
    return indices


# ---------------------------------------------------------------------------
# Захват камеры в отдельном worker-thread
# ---------------------------------------------------------------------------
class CameraCaptureLoop(QtCore.QObject):
    """Лёгкий worker для чтения кадров из cv2.VideoCapture.

    Он намеренно не трогает QPixmap/QWidget и вообще GUI. Только читает кадры
    под общим lock и отдаёт последний np.ndarray через Qt-signal. Обработка
    кадра остаётся в основном QTimer-пайплайне КругоЗора, чтобы не ломать
    хромакей, динамический кроп, Телемост, PTZ и виртуальную камеру одним
    героическим рефакторингом, после которого обычно ищут виноватого.
    """

    frame_ready = QtCore.pyqtSignal(object)
    no_frame = QtCore.pyqtSignal(int)
    stopped = QtCore.pyqtSignal()

    def __init__(self, lock: threading.RLock):
        super().__init__()
        self._lock = lock
        self._cap = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._fps = 30
        self._camera_index = -1
        self._missed = 0

    def is_running(self) -> bool:
        th = self._thread
        return bool(th is not None and th.is_alive())

    def set_capture(self, cap, camera_index: int, fps: int) -> None:
        self.stop_capture(release=False, wait=True)
        self._cap = cap
        self._camera_index = int(camera_index)
        self._fps = max(1, int(fps or 30))
        self._missed = 0
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"KrugoZorCapture-{self._camera_index}",
            daemon=True,
        )
        self._thread.start()

    def stop_capture(self, release: bool = True, wait: bool = True) -> None:
        self._stop_event.set()
        th = self._thread
        if wait and th is not None and th.is_alive() and th is not threading.current_thread():
            th.join(timeout=1.2)
        self._thread = None
        if release:
            with self._lock:
                cap = self._cap
                self._cap = None
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass
        else:
            self._cap = None
        self.stopped.emit()

    def _run(self) -> None:
        interval = 1.0 / max(1, int(self._fps or 30))
        next_time = time.perf_counter()
        while not self._stop_event.is_set():
            frame = None
            ok = False
            with self._lock:
                cap = self._cap
                if cap is not None:
                    try:
                        ok, frame = cap.read()
                    except Exception:
                        ok, frame = False, None
            if ok and frame is not None:
                self._missed = 0
                self.frame_ready.emit(frame)
            else:
                self._missed += 1
                if self._missed in (1, 30, 100):
                    self.no_frame.emit(int(self._missed))
            next_time += interval
            delay = next_time - time.perf_counter()
            if delay < 0:
                next_time = time.perf_counter()
                delay = 0.001
            self._stop_event.wait(min(delay, 0.05))

def get_windows_camera_names() -> list[str]:
    """Возвращает человекочитаемые имена камер Windows.
    OpenCV сам по себе обычно отдаёт только индексы, поэтому берём
    FriendlyName из системного списка устройств. Если PowerShell недоступен,
    тихо возвращаем пустой список — программа должна стартовать всегда."""
    if os.name != "nt":
        return []
    try:
        ps = (
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
            "$items = Get-CimInstance Win32_PnPEntity | "
            "Where-Object { $_.PNPClass -in @('Camera','Image') -or "
            "$_.Name -match 'camera|webcam|video|brio|insta|obs' }; "
            "$items | Sort-Object Name | ForEach-Object { $_.Name }"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            timeout=2, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode != 0:
            return []
        names = []
        seen = set()
        for line in completed.stdout.splitlines():
            name = line.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
        return names
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Модели состояния
# ---------------------------------------------------------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

@dataclass
class PickSlot:
    """Один слот пипетки. До 4-х слотов в ChromaConfig.picks.
    A и B по умолчанию включены; C и D — выключены (создаются про запас)."""
    enabled: bool = False
    color:   list = None     # [r, g, b] — цвет, выбранный пипеткой, или None
    tol:     int  = 30       # Радиус допуска в RGB-пространстве (евклидово)
    pos:     list = None     # [x, y] — точка на исходном кадре, для метки на превью

@dataclass
class ChromaConfig:
    """Настройки хромакея. Все включённые источники складываются в одну
    маску через ИЛИ: пипетки (включённые) + HSV-диапазон (если use_hsv).
    Это позволяет одной картинкой подавлять, например, и зелёный фон,
    и куски синей кофты — параллельно."""
    enabled:    bool  = True
    picks:      list  = None       # 4 × PickSlot — заполняется в __post_init__
    use_hsv:    bool  = True
    h_min:      int   = 70
    h_max:      int   = 108
    s_min:      int   = 0
    s_max:      int   = 58
    v_min:      int   = 135
    v_max:      int   = 235
    h_wrap:     bool  = False      # «кольцевой» H-диапазон (h_min > h_max)
    feather:    int   = 15         # Размытие края кеинга (px Гаусса)
    ui_opacity: float = 1.0
    persist:    bool  = True

    def __post_init__(self):
        # Базовый профиль хромакея из рабочего config.json пользователя:
        # HSV-диапазон + три включённые пипетки.
        # Создаём список тут, чтобы не делиться mutable default между
        # экземплярами dataclass'а.
        if self.picks is None:
            self.picks = [
                PickSlot(enabled=True,  color=[179, 185, 183], tol=22, pos=[610, 35]),
                PickSlot(enabled=True,  color=[150, 156, 156], tol=14, pos=[73, 266]),
                PickSlot(enabled=True,  color=[162, 171, 172], tol=12, pos=[130, 161]),
                PickSlot(enabled=False, color=[98, 94, 91],    tol=21, pos=[9, 453]),
            ]
        else:
            # Если пришло из config.json — нормализуем длину до 4-х.
            # Каждый элемент мог прийти как dict (после json.load).
            normalized = []
            for i in range(4):
                if i < len(self.picks):
                    item = self.picks[i]
                    if isinstance(item, dict):
                        item = PickSlot(**item)
                    elif not isinstance(item, PickSlot):
                        item = PickSlot()
                    normalized.append(item)
                else:
                    normalized.append(PickSlot(enabled=(i < 2)))
            self.picks = normalized

@dataclass
class CropConfig:
    enabled: bool = True
    rect:    list = None

    def __post_init__(self):
        if self.rect is None:
            self.rect = [70, 33, 514, 437]

@dataclass
class DynamicCropConfig:
    """Изолированная сущность автокомпозиции.

    Не смешивается с ручным CropConfig: это временный вычисляемый кроп
    для плавающего окна. Виртуальная камера, хромакей и виньетка окна
    остаются на старом пайплайне.
    """
    enabled: bool = False
    # Положение лица внутри круга: эти параметры двигают стрелки.
    offset_x: float = 0.0
    offset_y: float = -0.14

    # Смещение самого композиционного круга относительно автоцентра.
    # Числа продублированы здесь намеренно: dataclass создаётся раньше блока констант.
    circle_offset_x: float = 0.0
    circle_offset_y: float = 0.0

    circle_to_head: float = 1.55
    crop_padding: float = 1.02
    analysis_scale_percent: int = 25
    # Живее, чем прототипные 0.2: меньше задержка за движением головы.
    # Совместимость со старой схемой. В v4 фактически используется как
    # position_smoothing, если в config.json нет новых полей.
    smoothing: float = 0.42
    position_smoothing: float = 0.42
    scale_smoothing: float = 0.22
    # center_dead_zone оставлен для совместимости. В v4 он = position_dead_zone.
    position_dead_zone: float = 0.06
    scale_dead_zone: float = 0.08
    # face_box = старая логика; eyes_ipd = якорь по глазам, масштаб по межзрачковому.
    tracking_mode: str = "eyes_ipd"
    fast_roi_tracking: bool = True
    face_roi_margin: float = 2.8
    detector_min_neighbors: int = 4
    # По умолчанию не тянем кроп к центру кадра при краткой потере лица.
    # Иначе картинка начинает дёргаться при каждом пропуске детектора.
    return_speed: float = 0.0
    # Мёртвая зона вокруг целевой позиции лица внутри круга.
    # Пока лицо остаётся внутри этой области, центр кропа не двигается.
    center_dead_zone: float = 0.06
    min_face_size_full_frame: int = 80
    vignette_panel_width: int = 360
    nudge_step: float = 0.01
    max_composition_offset: float = 0.5
    arrows_move_face: bool = True
    invert_arrows_x: bool = False
    invert_arrows_y: bool = False
    show_debug_view: bool = False
    detector: str = "mediapipe"

@dataclass
class DynamicBox:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0

    @property
    def size(self) -> float:
        return max(self.w, self.h)

@dataclass
class DynamicCircleState:
    cx: float
    cy: float
    diameter: float

@dataclass
class DynamicCropRuntimeState:
    # raw_face — последнее реальное обнаружение Haar Cascade.
    # previous_face используется для выбора ближайшего лица на следующем кадре,
    # как в head_vignette_tracker: сравниваем кандидатов с последней сырой целью,
    # а не с уже сглаженной рамкой.
    raw_face: DynamicBox | None = None
    previous_face: DynamicBox | None = None

    # face/circle — сглаженное состояние вывода динамического кропа.
    face: DynamicBox | None = None
    circle: DynamicCircleState | None = None

    # target_circle — прямой расчёт по текущему лицу.
    # stable_circle — тот же расчёт после мёртвой зоны, до финального сглаживания.
    # Разделение нужно, чтобы не смешивать детекцию, композицию и фактический crop.
    target_circle: DynamicCircleState | None = None
    stable_circle: DynamicCircleState | None = None
    crop_rect: list | None = None

    face_found: bool = False
    lost_frames: int = 0
    processed_frames: int = 0

@dataclass
class PTZConfig:
    """Безопасный контур PTZ.

    Управление идёт через OpenCV CAP_PROP_PAN/TILT/ZOOM. Это работает не со
    всеми камерами и драйверами, поэтому PTZ по умолчанию выключен и не
    считается критичным для основного видеопотока.
    """
    enabled: bool = False
    trigger_edge_guard: bool = True
    trigger_focus_vertical_thirds: bool = True
    edge_guard_percent: int = 10
    focus_third_percent: int = 33
    cooldown_frames: int = 8
    # Шаги не 1.0: для части UVC/PTZ-драйверов единица почти незаметна.
    # Пользователь может уменьшить их ползунками, если камера слишком резкая.
    pan_step: float = 8.0
    tilt_step: float = 8.0
    zoom_step: float = 4.0

    # Диапазоны ползунков физического положения. Это не «истина драйвера»,
    # а безопасная рабочая шкала для DirectShow/OpenCV: многие камеры не
    # отдают реальные min/max, поэтому пользователь двигает накопленное
    # командное значение. При необходимости диапазон можно расширить в коде
    # без ломки config.json.
    pan_min: float = -100.0
    pan_max: float = 100.0
    tilt_min: float = -100.0
    tilt_max: float = 100.0
    zoom_min: float = 0.0
    zoom_max: float = 200.0

    invert_pan: bool = False
    invert_tilt: bool = False
    invert_zoom: bool = False
    show_debug: bool = False
    home_pan: float | None = None
    home_tilt: float | None = None
    home_zoom: float | None = None
    home_offset_x: float = 0.0
    home_offset_y: float = -0.05
    home_circle_offset_x: float = 0.0
    home_circle_offset_y: float = 0.0

@dataclass
class PTZRuntimeState:
    cooldown: int = 0
    last_pan: float | None = None
    last_tilt: float | None = None
    last_zoom: float | None = None

    # Накопленные командные значения. Многие DirectShow/OpenCV-драйверы
    # возвращают cap.get(PAN/TILT/ZOOM) как 0 или старое значение, даже если
    # cap.set(...) принят. Если каждый раз считать от cap.get(), камера
    # получает одну и ту же команду и визуально «не подруливает».
    command_pan: float | None = None
    command_tilt: float | None = None
    command_zoom: float | None = None

    last_trigger: str = ""
    last_command: str = ""
    last_error: str = ""

@dataclass
class AppState:
    camera_index:    int   = 0
    camera_aliases:  dict  = field(default_factory=dict)
    always_on_top:   bool  = True
    click_through:   bool  = False
    window_mirror:   bool  = True
    vcam_enabled:    bool  = True
    vcam_mirror:     bool  = False
    circle_diameter: int   = 360
    pos_x:           int   = 3123
    pos_y:           int   = 10
    window_shape:    str   = "circle"
    vcam_fit:        str   = "letterbox"   # legacy, не используется в v17+
    window_opacity:  float = 1.0
    edge_feather:    int   = 20

    # Масштаб полезного изображения внутри круглого основного окна.
    # 100 = без уменьшения, 88 = запас ~12% под мягкую виньетку.
    window_content_scale: int = 100

    # Размер круглой виньетки в виртуальной камере. 100 = круг по меньшей
    # стороне кадра vcam, 88 = уменьшенный круг с большим запасом по краям.
    vcam_vignette_scale: int = 50

    # Слои главного предпросмотра в общем окне настроек.
    preview_show_pipettes: bool = True
    preview_show_crop:     bool = True
    preview_show_circle:   bool = True
    preview_show_dimming:  bool = True
    preview_mirror:       bool = False

    # ----- v17: виртуальная камера -----
    # Масштаб лица в кадре vcam: 50..200% (100 = «как есть»)
    vcam_scale:      int   = 78

    # Режим композиции:
    #   "passthrough" — отдаём кадр с кеингом как есть (фон не нужен)
    #   "background"  — простая подкладка фона под прозрачные пиксели
    #   "circle"      — режим «лицо в круг» (имитация аватарки Телемост)
    vcam_mode:       str   = "circle"

    # Обводить ли результат vcam круглой виньеткой (как в окне).
    # По умолчанию — False, чтобы апгрейд не менял внешний вид у
    # тех, кто уже использовал passthrough. Включается чекбоксом
    # в диалоге vcam.
    vcam_circle_overlay: bool = True

    # v13.3: «голый» режим — отдавать кадр 1:1 как с физической
    # камеры, в её нативном разрешении, без кеинга/виньетки/масштаба.
    # Зеркало применяется (это пользовательское решение, не обработка).
    # При смене этого флага vcam пере-стартует с новым разрешением.
    vcam_passthrough_native: bool = False

    # Путь к подложке виртуальной камеры. В режиме "circle" это нижний
    # слой: по умолчанию белый фон, при выборе файла — картинка-подложка.
    vcam_bg_path:    str   = ""

    # Цвет слоя аватарки для режима "circle". Это НЕ нижняя подложка,
    # а верхняя плашка с круглым вырезом. У Телемоста фон аватарки
    # не чёрный, поэтому дефолт сразу тёмно-серо-синий.
    vcam_avatar_bg_color: str = "#202128"

    # Параметры круга для режима "circle" (в координатах подложки):
    vcam_circle_x:        int  = 805  # центр круга, X
    vcam_circle_y:        int  = 461  # центр круга, Y
    vcam_circle_r:        int  = 292  # радиус круга
    vcam_circle_auto:     bool = False # автодетект отключён: круг задаётся вручную X/Y/R

# ---------------------------------------------------------------------------
# Масштаб полезного изображения внутри круглой виньетки
# ---------------------------------------------------------------------------
# Небольшой внутренний отступ решает сразу две проблемы:
#   1) края круга получают место под мягкий переход, не упираясь в границы;
#   2) в круг попадает чуть больше реальной сцены, то есть виртуальная камера
#      выглядит ближе к тому, что видит физическая камера в приложении.
WINDOW_CIRCLE_CONTENT_SCALE_DEFAULT = 0.88
VCAM_CIRCLE_CONTENT_SCALE           = 0.88

# ---------------------------------------------------------------------------
# Динамический кроп / автокомпозиция
# ---------------------------------------------------------------------------
DEFAULT_ANALYSIS_SCALE_PERCENT = 25
DEFAULT_SMOOTHING = 0.42
DEFAULT_CIRCLE_MARGIN = 2.0
MIN_FACE_SIZE_FULL_FRAME = 80
VIGNETTE_PANEL_WIDTH = 360
COMPOSITION_NUDGE_STEP = 0.01
MAX_COMPOSITION_OFFSET = 0.5
DEFAULT_DYNAMIC_CIRCLE_OFFSET_X = 0.0
DEFAULT_DYNAMIC_CIRCLE_OFFSET_Y = 0.0
DEFAULT_DYNAMIC_CROP_PADDING = 1.08
DEFAULT_DYNAMIC_RETURN_SPEED = 0.0
DEFAULT_DYNAMIC_CENTER_DEAD_ZONE = 0.12
# После потери лица не возвращаем кроп в центр сразу.
# Сначала удерживаем последнее стабильное положение, как в прототипе tracker.
DYNAMIC_CROP_RETURN_AFTER_LOST_FRAMES = 30

DYNAMIC_CROP_ANALYSIS_MIN = 25
DYNAMIC_CROP_ANALYSIS_MAX = 100
DYNAMIC_CROP_MIN_FACE_SIZE_FULL_FRAME = MIN_FACE_SIZE_FULL_FRAME
DYNAMIC_CROP_NUDGE_STEP = COMPOSITION_NUDGE_STEP
DYNAMIC_CROP_CIRCLE_STEP = 0.05
DYNAMIC_CROP_ANALYSIS_STEP = 5
DYNAMIC_CROP_MAX_OFFSET = MAX_COMPOSITION_OFFSET
DYNAMIC_CROP_MIN_CIRCLE_TO_HEAD = 1.0
DYNAMIC_CROP_MAX_CIRCLE_TO_HEAD = 4.0
DYNAMIC_CROP_PADDING = DEFAULT_DYNAMIC_CROP_PADDING

# ---------------------------------------------------------------------------
# Единая тема оформления для всех меню и диалогов
# ---------------------------------------------------------------------------
# Дефолтный QSS встроен в код, но если рядом со скриптом лежит файл
# style.qss — он перекрывает дефолт (см. _load_style ниже).
STYLE_QSS_DEFAULT = """
/* 
Встроенный стиль v3: интегрирован из пользовательского style.qss.
Если рядом с программой лежит внешний style.qss, он по-прежнему имеет приоритет.
*/
/*
style.qss — тема КругоЗор в визуальной логике CalcNumLock / Win11 Calculator.

Назначение:
  • единый тёмный стиль для диалогов, контекстного меню и меню трея;
  • мягкие hover/pressed-состояния;
  • Segoe UI Variable / Segoe UI;
  • скругления 4/8 px;
  • аккуратные QSlider, QSpinBox, QCheckBox, QRadioButton;
  • совместимость с текущей загрузкой STYLE_QSS в KruGoZor.pyw.

Файл положить рядом с KruGoZor.pyw под именем style.qss.
*/

/* -------------------------------------------------------------------------
   Базовая палитра
   ------------------------------------------------------------------------- */
* {
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 13px;
    outline: none;
}

QWidget,
QDialog,
QMessageBox {
    background-color: #202020;
    color: #FFFFFF;
}

QLabel {
    color: #FFFFFF;
    background: transparent;
}

QLabel:disabled {
    color: #5F5F5F;
}

QToolTip {
    background-color: #2B2B2B;
    color: #FFFFFF;
    border: 1px solid #3B3B3B;
    border-radius: 4px;
    padding: 4px 8px;
}

/* -------------------------------------------------------------------------
   Группы и контейнеры диалогов
   ------------------------------------------------------------------------- */
QGroupBox {
    color: #FFFFFF;
    background: transparent;
    border: 1px solid #2B2B2B;
    border-radius: 8px;
    margin-top: 10px;
    padding: 9px 7px 7px 7px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #A6A6A6;
    background-color: #202020;
}

QFrame {
    background: transparent;
    border: none;
}

QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #2D2D2D;
    background-color: #2D2D2D;
}

/* -------------------------------------------------------------------------
   Поля ввода
   ------------------------------------------------------------------------- */
QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox,
QPlainTextEdit,
QTextEdit {
    background-color: #323232;
    color: #FFFFFF;
    border: 1px solid #2B2B2B;
    border-radius: 4px;
    padding: 4px 7px;
    selection-background-color: #4CC2FF;
    selection-color: #000000;
}

QLineEdit:hover,
QComboBox:hover,
QSpinBox:hover,
QDoubleSpinBox:hover,
QPlainTextEdit:hover,
QTextEdit:hover {
    background-color: #3C3C3C;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QPlainTextEdit:focus,
QTextEdit:focus {
    border: 1px solid #4CC2FF;
    background-color: #323232;
}

QLineEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled,
QPlainTextEdit:disabled,
QTextEdit:disabled {
    color: #5F5F5F;
    background-color: #2A2A2A;
    border-color: #2B2B2B;
}

QSpinBox::up-button,
QSpinBox::down-button,
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button {
    background-color: #323232;
    border: none;
    width: 16px;
}

QSpinBox::up-button:hover,
QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover {
    background-color: #454545;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #2B2B2B;
    color: #FFFFFF;
    border: 1px solid #2B2B2B;
    selection-background-color: #454545;
    selection-color: #FFFFFF;
    padding: 4px;
}

/* -------------------------------------------------------------------------
   Кнопки
   ------------------------------------------------------------------------- */
QPushButton,
QToolButton {
    background-color: #323232;
    color: #FFFFFF;
    border: 1px solid #2B2B2B;
    border-radius: 4px;
    padding: 5px 14px;
    min-height: 26px;
    font-weight: 400;
}

QToolButton {
    padding: 2px 7px;
    min-width: 26px;
    min-height: 24px;
}

QPushButton:hover,
QToolButton:hover {
    background-color: #3C3C3C;
}

QPushButton:pressed,
QToolButton:pressed {
    background-color: #2A2A2A;
}

QPushButton:disabled,
QToolButton:disabled {
    color: #5F5F5F;
    background-color: #2A2A2A;
    border-color: #2B2B2B;
}

QPushButton:default {
    background-color: #4CC2FF;
    color: #000000;
    border: 1px solid #4CC2FF;
    font-weight: 600;
}

QPushButton:default:hover {
    background-color: #5DC9FF;
}

QPushButton:default:pressed {
    background-color: #3FB7F5;
}

/* -------------------------------------------------------------------------
   Чекбоксы и радиокнопки
   ------------------------------------------------------------------------- */
QCheckBox,
QRadioButton {
    color: #FFFFFF;
    background: transparent;
    spacing: 6px;
    padding: 2px 0;
}

QCheckBox:disabled,
QRadioButton:disabled {
    color: #5F5F5F;
}

QCheckBox::indicator,
QRadioButton::indicator {
    width: 14px;
    height: 14px;
}

QCheckBox::indicator:unchecked {
    background-color: #323232;
    border: 1px solid #5F5F5F;
    border-radius: 3px;
}

QCheckBox::indicator:unchecked:hover {
    background-color: #3C3C3C;
    border-color: #A6A6A6;
}

QCheckBox::indicator:checked {
    background-color: #4CC2FF;
    border: 1px solid #4CC2FF;
    border-radius: 3px;
}

QCheckBox::indicator:checked:hover {
    background-color: #5DC9FF;
    border-color: #5DC9FF;
}

QRadioButton::indicator:unchecked {
    background-color: #323232;
    border: 1px solid #5F5F5F;
    border-radius: 7px;
}

QRadioButton::indicator:unchecked:hover {
    background-color: #3C3C3C;
    border-color: #A6A6A6;
}

QRadioButton::indicator:checked {
    background: qradialgradient(
        cx: 0.5, cy: 0.5, radius: 0.5,
        stop: 0 #4CC2FF,
        stop: 0.44 #4CC2FF,
        stop: 0.48 #323232,
        stop: 1 #323232
    );
    border: 1px solid #4CC2FF;
    border-radius: 7px;
}

/* -------------------------------------------------------------------------
   Слайдеры
   ------------------------------------------------------------------------- */
QSlider {
    background: transparent;
}

QSlider::groove:horizontal {
    height: 4px;
    background-color: #2D2D2D;
    border: none;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background-color: #4CC2FF;
    border-radius: 2px;
}

QSlider::add-page:horizontal {
    background-color: #2D2D2D;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 13px;
    height: 13px;
    margin: -5px 0;
    background-color: #4CC2FF;
    border: none;
    border-radius: 6px;
}

QSlider::handle:horizontal:hover {
    background-color: #5DC9FF;
}

QSlider::handle:horizontal:pressed {
    background-color: #3FB7F5;
}

QSlider::groove:vertical {
    width: 4px;
    background-color: #2D2D2D;
    border: none;
    border-radius: 2px;
}

QSlider::handle:vertical {
    width: 13px;
    height: 13px;
    margin: 0 -5px;
    background-color: #4CC2FF;
    border: none;
    border-radius: 6px;
}

/* -------------------------------------------------------------------------
   Меню: контекстное и трей
   ------------------------------------------------------------------------- */
QMenu {
    background-color: #2B2B2B;
    color: #FFFFFF;
    border: 1px solid #2B2B2B;
    border-radius: 8px;
    padding: 4px;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 13px;
}

QMenu::item {
    background: transparent;
    color: #FFFFFF;
    padding: 6px 18px 6px 24px;
    min-height: 18px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #454545;
}

QMenu::item:pressed {
    background-color: #333333;
}

QMenu::item:disabled {
    color: #5F5F5F;
}

QMenu::separator {
    height: 1px;
    background-color: #2D2D2D;
    margin: 4px 8px;
}

QMenu::indicator {
    width: 14px;
    height: 14px;
    margin-left: 4px;
}

QMenu::indicator:non-exclusive:unchecked {
    background-color: #323232;
    border: 1px solid #5F5F5F;
    border-radius: 3px;
}

QMenu::indicator:non-exclusive:checked {
    background-color: #4CC2FF;
    border: 1px solid #4CC2FF;
    border-radius: 3px;
}

QMenu::indicator:exclusive:unchecked {
    background-color: #323232;
    border: 1px solid #5F5F5F;
    border-radius: 7px;
}

QMenu::indicator:exclusive:checked {
    background: qradialgradient(
        cx: 0.5, cy: 0.5, radius: 0.5,
        stop: 0 #4CC2FF,
        stop: 0.44 #4CC2FF,
        stop: 0.48 #323232,
        stop: 1 #323232
    );
    border: 1px solid #4CC2FF;
    border-radius: 7px;
}

QMenu::right-arrow {
    width: 9px;
    height: 9px;
}

/* -------------------------------------------------------------------------
   Таблицы / списки, если появятся в диалогах
   ------------------------------------------------------------------------- */
QListWidget,
QListView,
QTableWidget,
QTableView,
QTreeWidget,
QTreeView {
    background-color: #2B2B2B;
    alternate-background-color: #323232;
    color: #FFFFFF;
    border: 1px solid #2B2B2B;
    border-radius: 4px;
    gridline-color: #2D2D2D;
    selection-background-color: #4CC2FF;
    selection-color: #000000;
}

QListWidget::item,
QListView::item,
QTableWidget::item,
QTableView::item,
QTreeWidget::item,
QTreeView::item {
    color: #FFFFFF;
    padding: 3px 5px;
}

QListWidget::item:selected,
QListView::item:selected,
QTableWidget::item:selected,
QTableView::item:selected,
QTreeWidget::item:selected,
QTreeView::item:selected {
    background-color: #4CC2FF;
    color: #000000;
}

QHeaderView::section {
    background-color: #323232;
    color: #FFFFFF;
    border: 1px solid #2B2B2B;
    padding: 4px 6px;
}

QTableCornerButton::section {
    background-color: #323232;
    border: 1px solid #2B2B2B;
}

/* -------------------------------------------------------------------------
   Скроллбары
   ------------------------------------------------------------------------- */
QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #202020;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 2px 4px 0;
}

QScrollBar::handle:vertical {
    background-color: #5F5F5F;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A6A6A6;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0 4px 2px 4px;
}

QScrollBar::handle:horizontal {
    background-color: #5F5F5F;
    border-radius: 3px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #A6A6A6;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

/* -------------------------------------------------------------------------
   Диалоги сообщений
   ------------------------------------------------------------------------- */
QMessageBox QLabel {
    color: #FFFFFF;
    background: transparent;
}

QMessageBox QPushButton {
    min-width: 82px;
}

/* -------------------------------------------------------------------------
   Специальные роли, которые безопасно сработают только при object/property
   ------------------------------------------------------------------------- */
QLabel[role="dim"],
QLabel[labelRole="dim"] {
    color: #A6A6A6;
}

QLabel[role="error"],
QLabel[labelRole="error"] {
    color: #FF8A8A;
}

QLabel[role="ok"],
QLabel[labelRole="ok"] {
    color: #7DDA9F;
}

QPushButton[role="danger"] {
    background-color: #5A2525;
    color: #FFFFFF;
    border-color: #6A3030;
}

QPushButton[role="danger"]:hover {
    background-color: #6A3030;
}

QPushButton[role="danger"]:pressed {
    background-color: #4A2020;
}

/* КругоЗор: токены оверлея предпросмотра
--kgz-preview-line-width: 0.23;
--kgz-preview-crop-circle-extra-width: 0.70;
--kgz-preview-manual-crop: #2ea8ff;
--kgz-preview-inactive-crop: #68727e;
--kgz-preview-dynamic-crop: #ffcc4d;
--kgz-preview-composition-circle: #ffd166;
--kgz-preview-face-capture: #2ea8ff;
--kgz-preview-drag-crop: #ad7cff;
--kgz-preview-pipette-border: #ffffff;
--kgz-preview-crosshair: #dce6f0;
*/


/* -------------------------------------------------------------------------
   КругоЗор v8: гребёнка вкладок настроек
   ------------------------------------------------------------------------- */
QTabWidget#SettingsTabs::pane {
    border: 1px solid #3A3A3A;
    border-radius: 8px;
    top: -1px;
    background: #202020;
}

QTabWidget#SettingsTabs QTabBar::tab {
    background: #252525;
    color: #D6D6D6;
    border: 1px solid #3A3A3A;
    border-bottom-color: #2A2A2A;
    padding: 6px 14px;
    min-width: 120px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    margin-right: 2px;
}

QTabWidget#SettingsTabs QTabBar::tab:selected {
    background: #303030;
    color: #FFFFFF;
    border-bottom-color: #303030;
}

QTabWidget#SettingsTabs QTabBar::tab:hover:!selected {
    background: #2C2C2C;
    color: #FFFFFF;
}

QTabWidget#SettingsTabs QScrollArea {
    background: transparent;
    border: none;
}

"""

# Принудительные fixup-правила дописываются ПОСЛЕ пользовательского style.qss,
# чтобы базовая читабельность не зависела от того, какой старый стиль лежит
# рядом со скриптом. Это устраняет ситуацию, когда часть текста в диалогах
# внезапно рисуется чёрным по тёмному фону.
STYLE_QSS_FIXUPS = """
QWidget, QDialog, QMessageBox, QGroupBox, QLabel,
QCheckBox, QRadioButton, QPushButton, QSpinBox {
    color: #eee;
}
QGroupBox::title { color: #eee; }
QSpinBox {
    selection-background-color: #4a8;
    selection-color: #111;
}
"""

def _load_style() -> str:
    """Возвращает содержимое style.qss рядом со скриптом, если он есть.
    Иначе возвращает встроенный STYLE_QSS_DEFAULT и одноразово создаёт
    style.qss рядом — чтобы пользователь мог его править."""
    try:
        if os.path.exists(STYLE_FILE):
            with open(STYLE_FILE, "r", encoding="utf-8") as f:
                return f.read() + "\n" + STYLE_QSS_FIXUPS
        # Файла нет — создаём, чтобы пользователь видел и мог поправить
        with open(STYLE_FILE, "w", encoding="utf-8") as f:
            f.write(STYLE_QSS_DEFAULT)
    except Exception:
        # Ошибки чтения/записи стиля — не критичны, просто берём дефолт
        pass
    return STYLE_QSS_DEFAULT + "\n" + STYLE_QSS_FIXUPS

# Загружаем на старте — один источник стиля для всего приложения
STYLE_QSS = _load_style()

def _style_token(name: str, default: str) -> str:
    """Возвращает CSS-like токен из style.qss.

    Токены пишутся так:
        --kgz-preview-face-capture: #2ea8ff;
    QSS их игнорирует как неизвестные свойства, а Python использует
    для цветов/толщин оверлея главного предпросмотра.
    """
    try:
        m = re.search(r"--kgz-" + re.escape(name) + r"\s*:\s*([^;\n]+)", STYLE_QSS)
        if m:
            value = m.group(1).strip()
            if value:
                return value
    except Exception:
        pass
    return default

def _style_float_token(name: str, default: float) -> float:
    try:
        raw = _style_token(name, str(default)).replace(",", ".")
        return float(raw)
    except Exception:
        return float(default)

# ---------------------------------------------------------------------------
# Реестр действий, привязываемых к горячим клавишам.
# ---------------------------------------------------------------------------
# id → (человекочитаемое название, последовательность по умолчанию,
#        способ применения):
#   "menu" — обновляет setShortcut на QAction; ярлык виден в меню.
#   "shortcut" — создаёт QShortcut с приложение-уровневым контекстом.
HOTKEY_DEFINITIONS = (
    # id              title                                default   kind        action_attr
    ("chroma_toggle",  "Хромакей: вкл/выкл",                "K",      "menu",     "act_chroma"),
    ("chroma_cfg",     "Хромакей: открыть настройки",       "Ctrl+K", "menu",     "act_chroma_cfg"),
    ("vcam_toggle",    "Виртуальная камера: вкл/выкл",      "V",      "shortcut", None),
    ("vcam_mirror",    "Виртуальная камера: зеркало",       "B",      "shortcut", None),
    ("window_mirror",  "Окно: зеркало",                     "M",      "shortcut", None),
    ("dynamic_crop_toggle", "Динамический кроп: вкл/выкл",   "",       "menu",     "act_dynamic_crop"),
    ("scale_up",       "Окно: увеличить",                  "+",  "shortcut", None),
    ("scale_up_alt",   "Окно: увеличить",                  "=",  "shortcut", None),
    ("scale_down",     "Окно: уменьшить",                  "-",  "shortcut", None),
    ("dynamic_left",   "Динамический кроп: цель влево",      "Left",   "shortcut", None),
    ("dynamic_right",  "Динамический кроп: цель вправо",     "Right",  "shortcut", None),
    ("dynamic_up",     "Динамический кроп: цель вверх",      "Up",     "shortcut", None),
    ("dynamic_down",   "Динамический кроп: цель вниз",       "Down",   "shortcut", None),
    ("dynamic_analysis_down", "Динамический кроп: анализ -",  "[",      "shortcut", None),
    ("dynamic_analysis_up",   "Динамический кроп: анализ +",  "]",      "shortcut", None),
    ("dynamic_analysis_down_alt", "Динамический кроп: анализ -", "1",   "shortcut", None),
    ("dynamic_analysis_up_alt",   "Динамический кроп: анализ +", "2",   "shortcut", None),
    ("dynamic_reset",  "Камера и цель: к базовому положению", "0",      "shortcut", None),
    ("hotkeys",        "Открыть «Hotkeys»",                 "",       "menu",     "act_hotkeys"),
    ("about",          "О программе",                       "",       "menu",     "act_about"),
    ("quit",           "Выход",                             "Ctrl+Q", "menu",     "act_exit"),
)

DEFAULT_HOTKEYS = {hid: seq for hid, _t, seq, _k, _a in HOTKEY_DEFINITIONS}


class ChromaDialog(QDialog):
    """Единое окно настроек: камера, хромакей, кроп, виньетка и виртуальная камера."""

    PICK_LABELS = ("A", "B", "C", "D")

    def __init__(self, parent, chroma: ChromaConfig, get_frame_callable, owner=None):
        super().__init__(parent)
        self.setWindowTitle("КругоЗор — Хромакей / Виньетка / Кроп / Виртуальная камера")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.setStyleSheet(STYLE_QSS)
        self.resize(980, 760)
        self.setMinimumWidth(800)

        self.chroma = chroma
        self.get_frame = get_frame_callable
        self.owner = owner
        self._pick_target = None
        self._preview_mode = "orig"
        self._crop_dragging = False
        self._crop_start_pt = None
        self._crop_end_pt = None

        # ------------------------------------------------------------------
        # Верхняя строка: выбор камеры раскрывающимся списком
        # ------------------------------------------------------------------
        self.camera_combo = QtWidgets.QComboBox(self)
        self.camera_combo.setMinimumWidth(140)
        self.camera_refresh_btn = QPushButton("↻")
        self.camera_refresh_btn.setToolTip("Обновить список камер")
        self.camera_rename_btn = QPushButton("Переименовать…")
        self.camera_status_lbl = QLabel("")
        self.camera_status_lbl.setStyleSheet("color:#aeb7c2;")

        # ------------------------------------------------------------------
        # Хромакей
        # ------------------------------------------------------------------
        self.enabled_chk = QCheckBox("Включён хромакей")
        font = self.enabled_chk.font()
        font.setBold(True)
        self.enabled_chk.setFont(font)

        self._slot_widgets = []
        for i in range(4):
            chk = QCheckBox()
            pick_btn = QPushButton(self.PICK_LABELS[i])
            pick_btn.setToolTip(f"Выбрать цвет пипетки {self.PICK_LABELS[i]}")
            swatch = QLabel()
            swatch.setFixedSize(22, 22)
            rgb_lbl = QLabel("-")
            rgb_lbl.setStyleSheet("min-width:120px;")
            tol_sld = QSlider(Qt.Horizontal)
            tol_sld.setRange(0, 255)
            tol_spin = QSpinBox()
            tol_spin.setRange(0, 255)
            tol_spin.setFixedWidth(58)
            self._slot_widgets.append((chk, pick_btn, swatch, rgb_lbl, tol_sld, tol_spin))

        self.use_hsv_chk = QCheckBox("Использовать HSV-диапазон")
        self.h_wrap_chk = QCheckBox("Кольцевой H")
        self.hsv_pick_btn = QPushButton("Заполнить HSV из активной пипетки")
        self._hsv_fields = (("H", "h", 0, 179), ("S", "s", 0, 255), ("V", "v", 0, 255))
        self._hsv_sliders = {}
        self._hsv_spins = {}
        for _label, key, lo, hi in self._hsv_fields:
            for end_name in ("min", "max"):
                full = f"{key}_{end_name}"
                sld = QSlider(Qt.Horizontal)
                sld.setRange(lo, hi)
                spn = QSpinBox()
                spn.setRange(lo, hi)
                spn.setFixedWidth(58)
                self._hsv_sliders[full] = sld
                self._hsv_spins[full] = spn

        self.feather_sld = QSlider(Qt.Horizontal)
        self.feather_sld.setRange(0, 101)
        self.feather_lbl = QLabel("Мягкость кеинга")
        self.vignette_sld = QSlider(Qt.Horizontal)
        self.vignette_sld.setRange(0, 100)
        self.vignette_lbl = QLabel("Мягкость")
        self.window_scale_sld = QSlider(Qt.Horizontal)
        self.window_scale_sld.setRange(70, 100)
        self.window_scale_lbl = QLabel("")
        self.persist_chk = QCheckBox("Сохранять настройки (config.json)")

        self.mode_orig_rb = QtWidgets.QRadioButton("Оригинал")
        self.mode_result_rb = QtWidgets.QRadioButton("Результат")
        self.mode_mask_rb = QtWidgets.QRadioButton("Маска")
        self.mode_orig_rb.setChecked(True)
        mode_grp = QtWidgets.QButtonGroup(self)
        mode_grp.addButton(self.mode_orig_rb)
        mode_grp.addButton(self.mode_result_rb)
        mode_grp.addButton(self.mode_mask_rb)

        self.layer_pipettes_chk = QCheckBox("Пипетки")
        self.layer_crop_chk = QCheckBox("Кроп")
        self.layer_circle_chk = QCheckBox("Круг")
        self.layer_dim_chk = QCheckBox("Затенение")
        self.preview_mirror_chk = QCheckBox("Зеркально")
        self.preview_mirror_chk.setToolTip("Зеркалит только главный предпросмотр. Плавающее окно и виртуальная камера не меняются.")
        for _w in (self.layer_pipettes_chk, self.layer_crop_chk,
                   self.layer_circle_chk, self.layer_dim_chk):
            _w.setChecked(True)

        self.preview_label = QLabel(self)
        self.preview_label.setMinimumSize(320, 180)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background:#111923; border:1px solid #2d3b49; border-radius:6px;")
        self.preview_label.installEventFilter(self)

        self.vignette_preview_lbl = QLabel(self)
        self.vignette_preview_lbl.setMinimumSize(160, 90)
        self.vignette_preview_lbl.setAlignment(Qt.AlignCenter)
        self.vignette_preview_lbl.setStyleSheet("background:#111923; border:1px solid #2d3b49; border-radius:6px;")

        self.vcam_preview_lbl = QLabel(self)
        self.vcam_preview_lbl.setMinimumSize(160, 90)
        self.vcam_preview_lbl.setAlignment(Qt.AlignCenter)
        self.vcam_preview_lbl.setStyleSheet("background:#111923; border:1px solid #2d3b49; border-radius:6px;")

        # ------------------------------------------------------------------
        # Кроп внутри этого же окна
        # ------------------------------------------------------------------
        self.crop_enabled_chk = QCheckBox("Кроп включён")
        self.crop_hint_lbl = QLabel("ЛКМ по главному предпросмотру — выделить область кропа. ПКМ — сбросить выделение. Кроп влияет только на плавающее окно и превью виньетки; виртуальная камера получает полный кадр.")
        self.crop_hint_lbl.setWordWrap(True)
        self.crop_hint_lbl.setStyleSheet("color:#aeb7c2;")
        self.crop_rect_lbl = QLabel("Кроп: —")
        self.crop_reset_btn = QPushButton("Сбросить кроп")
        self.crop_capture_btn = QPushButton("Взять весь кадр")
        self.crop_off_rb = QtWidgets.QRadioButton("Выключен")
        self.crop_manual_rb = QtWidgets.QRadioButton("Включен")
        self.crop_dynamic_rb = QtWidgets.QRadioButton("Динамический")
        self.crop_mode_group = QtWidgets.QButtonGroup(self)
        self.crop_mode_group.setExclusive(True)
        self.crop_mode_group.addButton(self.crop_off_rb)
        self.crop_mode_group.addButton(self.crop_manual_rb)
        self.crop_mode_group.addButton(self.crop_dynamic_rb)

        def _mk_slider(lo: int, hi: int, value: int = 0) -> QSlider:
            sld = QSlider(Qt.Horizontal)
            sld.setRange(int(lo), int(hi))
            sld.setValue(int(value))
            sld.setMinimumWidth(120)
            return sld

        self.dynamic_circle_sld = _mk_slider(100, 400, 200)
        self.dynamic_circle_x_sld = _mk_slider(-50, 50, 0)
        self.dynamic_circle_y_sld = _mk_slider(-50, 50, 0)
        self.dynamic_face_x_sld = _mk_slider(-50, 50, 0)
        self.dynamic_face_y_sld = _mk_slider(-50, 50, -5)
        self.dynamic_padding_sld = _mk_slider(100, 160, 108)
        self.dynamic_smoothing_sld = _mk_slider(0, 80, 42)
        self.dynamic_scale_smoothing_sld = _mk_slider(0, 80, 22)
        self.dynamic_return_speed_sld = _mk_slider(0, 100, 0)
        self.dynamic_center_dead_zone_sld = _mk_slider(0, 30, 6)
        self.dynamic_scale_dead_zone_sld = _mk_slider(0, 30, 8)
        self.dynamic_max_offset_sld = _mk_slider(5, 100, 50)
        self.dynamic_analysis_sld = _mk_slider(DYNAMIC_CROP_ANALYSIS_MIN, DYNAMIC_CROP_ANALYSIS_MAX, DEFAULT_ANALYSIS_SCALE_PERCENT)
        self.dynamic_min_face_sld = _mk_slider(24, 600, MIN_FACE_SIZE_FULL_FRAME)
        self.dynamic_panel_width_sld = _mk_slider(120, 1000, VIGNETTE_PANEL_WIDTH)
        self.dynamic_nudge_sld = _mk_slider(1, 100, 10)
        self.dynamic_tracking_mode_combo = QtWidgets.QComboBox(self)
        self.dynamic_tracking_mode_combo.addItem("Глаза + межзрачковое расстояние", "eyes_ipd")
        self.dynamic_tracking_mode_combo.addItem("Рамка лица", "face_box")
        self.dynamic_tracking_mode_combo.setToolTip("Глаза + IPD: позиция по центру между глазами, масштаб сначала по межзрачковому расстоянию; Рамка лица: старая логика по размеру лица.")

        self.dynamic_detector_combo = QtWidgets.QComboBox(self)
        self.dynamic_detector_combo.addItem("MediaPipe / landmarks", "mediapipe")
        self.dynamic_detector_combo.addItem("OpenCV Haar", "haar")
        self.dynamic_detector_combo.setToolTip("MediaPipe использует landmarks и точку между глазами; если mediapipe не установлен, модуль сам откатится на Haar.")

        self.dynamic_circle_val_lbl = QLabel("")
        self.dynamic_circle_x_val_lbl = QLabel("")
        self.dynamic_circle_y_val_lbl = QLabel("")
        self.dynamic_face_x_val_lbl = QLabel("")
        self.dynamic_face_y_val_lbl = QLabel("")
        self.dynamic_padding_val_lbl = QLabel("")
        self.dynamic_smoothing_val_lbl = QLabel("")
        self.dynamic_scale_smoothing_val_lbl = QLabel("")
        self.dynamic_return_speed_val_lbl = QLabel("")
        self.dynamic_center_dead_zone_val_lbl = QLabel("")
        self.dynamic_scale_dead_zone_val_lbl = QLabel("")
        self.dynamic_max_offset_val_lbl = QLabel("")
        self.dynamic_analysis_val_lbl = QLabel("")
        self.dynamic_min_face_val_lbl = QLabel("")
        self.dynamic_panel_width_val_lbl = QLabel("")
        self.dynamic_nudge_val_lbl = QLabel("")
        for _lbl in (
            self.dynamic_circle_val_lbl, self.dynamic_circle_x_val_lbl, self.dynamic_circle_y_val_lbl,
            self.dynamic_face_x_val_lbl, self.dynamic_face_y_val_lbl, self.dynamic_padding_val_lbl,
            self.dynamic_smoothing_val_lbl, self.dynamic_scale_smoothing_val_lbl,
            self.dynamic_return_speed_val_lbl, self.dynamic_center_dead_zone_val_lbl, self.dynamic_scale_dead_zone_val_lbl,
            self.dynamic_max_offset_val_lbl, self.dynamic_analysis_val_lbl, self.dynamic_min_face_val_lbl, self.dynamic_panel_width_val_lbl,
            self.dynamic_nudge_val_lbl,
        ):
            _lbl.setMinimumWidth(46)
            _lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            _lbl.setStyleSheet("color:#aeb7c2;")

        self.dynamic_arrows_move_face_chk = QCheckBox("Стрелки двигают лицо в круге")
        self.dynamic_invert_x_chk = QCheckBox("Инвертировать ← / →")
        self.dynamic_invert_y_chk = QCheckBox("Инвертировать ↑ / ↓")
        self.dynamic_auto_center_btn = QPushButton("Автоцентр")
        self.dynamic_capture_btn = QPushButton("Захватить")
        self.dynamic_reset_params_btn = QPushButton("Сброс")

        # ------------------------------------------------------------------
        # PTZ: физическое смещение камеры как запасной контур для динамического кропа
        # ------------------------------------------------------------------
        self.ptz_enabled_chk = QCheckBox("Включить PTZ-подруливание")
        self.ptz_edge_guard_chk = QCheckBox("Триггер: касание зоны запаса края изображения")
        self.ptz_focus_thirds_chk = QCheckBox("Триггер: фокусная точка в верхней/нижней трети")
        self.ptz_invert_pan_chk = QCheckBox("Инвертировать Pan")
        self.ptz_invert_tilt_chk = QCheckBox("Инвертировать Tilt")
        self.ptz_invert_zoom_chk = QCheckBox("Инвертировать Zoom")
        self.ptz_show_debug_chk = QCheckBox("Показывать PTZ-разметку")

        self.ptz_edge_guard_sld = _mk_slider(0, 30, 10)
        self.ptz_focus_third_sld = _mk_slider(20, 45, 33)
        self.ptz_cooldown_sld = _mk_slider(1, 60, 8)
        self.ptz_pan_step_sld = _mk_slider(1, 100, 10)
        self.ptz_tilt_step_sld = _mk_slider(1, 100, 10)
        self.ptz_zoom_step_sld = _mk_slider(1, 100, 10)

        # Ползунки физического положения камеры. Значения умножены на 10,
        # чтобы можно было двигать камеру дробными командами 0.1.
        self.ptz_pan_pos_sld = _mk_slider(-1000, 1000, 0)
        self.ptz_tilt_pos_sld = _mk_slider(-1000, 1000, 0)
        self.ptz_zoom_pos_sld = _mk_slider(0, 2000, 0)

        self.ptz_edge_guard_val_lbl = QLabel("")
        self.ptz_focus_third_val_lbl = QLabel("")
        self.ptz_cooldown_val_lbl = QLabel("")
        self.ptz_pan_step_val_lbl = QLabel("")
        self.ptz_tilt_step_val_lbl = QLabel("")
        self.ptz_zoom_step_val_lbl = QLabel("")
        self.ptz_pan_pos_val_lbl = QLabel("")
        self.ptz_tilt_pos_val_lbl = QLabel("")
        self.ptz_zoom_pos_val_lbl = QLabel("")
        self.ptz_status_lbl = QLabel("PTZ: выключен")
        self.ptz_status_lbl.setStyleSheet("color:#aeb7c2;")
        for _lbl in (
            self.ptz_edge_guard_val_lbl, self.ptz_focus_third_val_lbl,
            self.ptz_cooldown_val_lbl, self.ptz_pan_step_val_lbl,
            self.ptz_tilt_step_val_lbl, self.ptz_zoom_step_val_lbl,
            self.ptz_pan_pos_val_lbl, self.ptz_tilt_pos_val_lbl, self.ptz_zoom_pos_val_lbl,
        ):
            _lbl.setMinimumWidth(46)
            _lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            _lbl.setStyleSheet("color:#aeb7c2;")

        self.ptz_left_btn = QPushButton("← Pan")
        self.ptz_right_btn = QPushButton("Pan →")
        self.ptz_up_btn = QPushButton("↑ Tilt")
        self.ptz_down_btn = QPushButton("Tilt ↓")
        self.ptz_zoom_in_btn = QPushButton("Zoom +")
        self.ptz_zoom_out_btn = QPushButton("Zoom −")

        # Эти кнопки всегда отправляют физическую PTZ-команду.
        # Нужны для проверки камеры, потому что основные Pan/Tilt в режиме
        # динамического кропа осознанно двигают композиционную цель.
        self.ptz_phys_left_btn = QPushButton("Физ. ←")
        self.ptz_phys_right_btn = QPushButton("Физ. →")
        self.ptz_phys_up_btn = QPushButton("Физ. ↑")
        self.ptz_phys_down_btn = QPushButton("Физ. ↓")
        self.ptz_read_position_btn = QPushButton("Считать из камеры")

        self.ptz_remember_home_btn = QPushButton("Запомнить базу")
        self.ptz_return_home_btn = QPushButton("0: К базе")

        self._ptz_setting_sliders = (
            self.ptz_edge_guard_sld, self.ptz_focus_third_sld,
            self.ptz_cooldown_sld, self.ptz_pan_step_sld,
            self.ptz_tilt_step_sld, self.ptz_zoom_step_sld,
        )
        self._ptz_position_sliders = (
            self.ptz_pan_pos_sld, self.ptz_tilt_pos_sld, self.ptz_zoom_pos_sld,
        )

        self._dynamic_setting_sliders = (
            self.dynamic_circle_sld,
            self.dynamic_circle_x_sld,
            self.dynamic_circle_y_sld,
            self.dynamic_face_x_sld,
            self.dynamic_face_y_sld,
            self.dynamic_padding_sld,
            self.dynamic_smoothing_sld,
            self.dynamic_scale_smoothing_sld,
            self.dynamic_return_speed_sld,
            self.dynamic_center_dead_zone_sld,
            self.dynamic_scale_dead_zone_sld,
            self.dynamic_max_offset_sld,
            self.dynamic_analysis_sld,
            self.dynamic_min_face_sld,
            self.dynamic_panel_width_sld,
            self.dynamic_nudge_sld,
        )
        self._dynamic_setting_widgets = self._dynamic_setting_sliders + (
            self.dynamic_tracking_mode_combo,
            self.dynamic_detector_combo,
            self.dynamic_arrows_move_face_chk,
            self.dynamic_invert_x_chk,
            self.dynamic_invert_y_chk,
            self.dynamic_auto_center_btn,
            self.dynamic_capture_btn,
            self.dynamic_reset_params_btn,
        )

        # ------------------------------------------------------------------
        # Виньетка: настройки окна, перенесённые из контекстного меню
        # ------------------------------------------------------------------
        self.vignette_on_top_chk = QCheckBox("Поверх всех окон")
        self.vignette_click_through_chk = QCheckBox("Прокликиваемый")
        self.vignette_mirror_chk = QCheckBox("Отразить")
        self.vignette_opacity_lbl = QLabel("Непрозрачность: 100%")
        self.vignette_opacity_sld = QSlider(Qt.Horizontal)
        self.vignette_opacity_sld.setRange(20, 100)

        # ------------------------------------------------------------------
        # Виртуальная камера внутри этого же окна
        # ------------------------------------------------------------------
        self.vcam_enabled_chk = QCheckBox("Включена виртуальная камера")
        self.vcam_mirror_chk = QCheckBox("Отразить зеркально")
        self.vcam_native_chk = QCheckBox("Отдавать как с физической камеры")
        self.vcam_native_chk.setToolTip("Полный кадр с физической камеры без кропа, хромакея, виньетки, масштаба и фона. Может применяться только зеркало виртуальной камеры.")
        self.vcam_circle_overlay_chk = QCheckBox("Круглая виньетка в виртуальной камере")

        self.vcam_scale_sld = QSlider(Qt.Horizontal)
        self.vcam_scale_sld.setRange(50, 200)
        self.vcam_scale_lbl = QLabel("Масштаб лица: 100%")
        self.vcam_vignette_size_sld = QSlider(Qt.Horizontal)
        self.vcam_vignette_size_sld.setRange(50, 100)
        self.vcam_vignette_size_lbl = QLabel("Размер виньетки: 100%")

        self.vcam_mode_combo = QtWidgets.QComboBox(self)
        self.vcam_mode_combo.addItem("Без фона", "passthrough")
        self.vcam_mode_combo.addItem("Простая подкладка", "background")
        self.vcam_mode_combo.addItem("Как в Телемост", "circle")

        self.vcam_bg_path_lbl = QLabel("Фон: не выбран")
        self.vcam_bg_path_lbl.setWordWrap(True)
        self.vcam_bg_path_lbl.setStyleSheet("color:#aeb7c2;")
        self.vcam_bg_load_btn = QPushButton("Выбрать подложку…")
        self.vcam_bg_telemost_btn = QPushButton("Для Телемоста")
        self.vcam_bg_clear_btn = QPushButton("Сброс")

        self.vcam_avatar_bg_lbl = QLabel("Фон аватарки: #202128")
        self.vcam_avatar_bg_lbl.setStyleSheet("color:#aeb7c2;")
        self.vcam_avatar_bg_color_btn = QPushButton("Цвет аватарки…")

        self.vcam_auto_chk = QCheckBox("Авто-детект круга при загрузке")
        self.vcam_cx_spin = QSpinBox(); self.vcam_cx_spin.setRange(0, 9999)
        self.vcam_cy_spin = QSpinBox(); self.vcam_cy_spin.setRange(0, 9999)
        self.vcam_cr_sld = QSlider(Qt.Horizontal); self.vcam_cr_sld.setRange(1, 9999)
        self.vcam_cr_spin = QSpinBox(); self.vcam_cr_spin.setRange(1, 9999)
        self.vcam_redetect_btn = QPushButton("Найти круг повторно")

        self.vcam_start_btn = QPushButton("Запустить")
        self.vcam_stop_btn = QPushButton("Остановить")
        self.vcam_restart_btn = QPushButton("Перезапустить")
        self.vcam_status_lbl = QLabel("")
        self.vcam_status_lbl.setStyleSheet("color:#aeb7c2;")

        self.reset_btn = QPushButton("Сбросить хромакей")
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setDefault(True)

        # ------------------------------------------------------------------
        # Компоновка
        # ------------------------------------------------------------------
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        camera_row = QHBoxLayout()
        camera_row.addWidget(QLabel("Камера:"))
        camera_row.addWidget(self.camera_combo)
        camera_row.addWidget(self.camera_refresh_btn)
        camera_row.addWidget(self.camera_rename_btn)
        camera_row.addStretch(1)
        root.addLayout(camera_row)

        preview_tools_row = QHBoxLayout()
        preview_tools_row.addWidget(self.mode_orig_rb)
        preview_tools_row.addWidget(self.mode_result_rb)
        preview_tools_row.addWidget(self.mode_mask_rb)
        preview_tools_row.addSpacing(10)
        preview_tools_row.addWidget(QLabel("Слои:"))
        preview_tools_row.addWidget(self.layer_pipettes_chk)
        preview_tools_row.addWidget(self.layer_crop_chk)
        preview_tools_row.addWidget(self.layer_circle_chk)
        preview_tools_row.addWidget(self.layer_dim_chk)
        preview_tools_row.addSpacing(10)
        preview_tools_row.addWidget(self.preview_mirror_chk)
        preview_tools_row.addStretch(1)
        root.addLayout(preview_tools_row)

        preview_row = QHBoxLayout()
        main_preview_box = QGroupBox("1. Главный предпросмотр")
        mp = QVBoxLayout(main_preview_box)
        mp.addWidget(self.preview_label, 1)
        preview_row.addWidget(main_preview_box, 3)

        side_preview_col = QVBoxLayout()
        vig_box = QGroupBox("2. Превью виньетки")
        vig_lay = QVBoxLayout(vig_box)
        vig_lay.addWidget(self.vignette_preview_lbl)
        vcam_prev_box = QGroupBox("3. Превью виртуальной камеры")
        vcp_lay = QVBoxLayout(vcam_prev_box)
        vcp_lay.addWidget(self.vcam_preview_lbl)
        side_preview_col.addWidget(vig_box)
        side_preview_col.addWidget(vcam_prev_box)
        preview_row.addLayout(side_preview_col, 1)
        root.addLayout(preview_row, 2)

        self.settings_tabs = QtWidgets.QTabWidget(self)
        self.settings_tabs.setObjectName("SettingsTabs")
        self.settings_tabs.addTab(self._tab_page(self._build_chroma_panel(), self._build_vignette_panel()), "Хромакей / виньетка")
        self.settings_tabs.addTab(self._tab_page(self._build_crop_panel()), "Кроп")
        self.settings_tabs.addTab(self._tab_page(self._build_vcam_panel()), "Виртуальная камера")
        self.settings_tabs.addTab(self._tab_page(self._build_ptz_panel()), "PTZ")
        root.addWidget(self.settings_tabs, 3)

        bottom = QHBoxLayout()
        bottom.addWidget(self.persist_chk)
        bottom.addStretch(1)
        bottom.addWidget(self.camera_status_lbl)
        bottom.addSpacing(12)
        bottom.addWidget(self.vcam_status_lbl)
        bottom.addSpacing(12)
        bottom.addWidget(self.reset_btn)
        bottom.addWidget(self.close_btn)
        root.addLayout(bottom)

        # ------------------------------------------------------------------
        # Сигналы
        # ------------------------------------------------------------------
        self._reload_camera_combo()
        self.camera_combo.currentIndexChanged.connect(self._on_camera_combo_changed)
        self.camera_refresh_btn.clicked.connect(self._on_camera_refresh)
        self.camera_rename_btn.clicked.connect(self._on_camera_rename)

        self.enabled_chk.toggled.connect(self._on_enabled_toggled)
        for i, (chk, pick_btn, _swatch, _rgb_lbl, tol_sld, tol_spin) in enumerate(self._slot_widgets):
            chk.toggled.connect(lambda v, idx=i: self._on_slot_enabled(idx, v))
            pick_btn.clicked.connect(lambda _=False, idx=i: self._begin_pick(idx))
            tol_sld.valueChanged.connect(lambda v, idx=i: self._on_slot_tol(idx, v))
            tol_spin.valueChanged.connect(lambda v, idx=i: self._on_slot_tol(idx, v))

        for key in ("h", "s", "v"):
            self._hsv_sliders[f"{key}_min"].valueChanged.connect(lambda v, k=key: self._on_hsv_changed(k, "min", v))
            self._hsv_sliders[f"{key}_max"].valueChanged.connect(lambda v, k=key: self._on_hsv_changed(k, "max", v))
            self._hsv_spins[f"{key}_min"].valueChanged.connect(lambda v, k=key: self._on_hsv_changed(k, "min", v))
            self._hsv_spins[f"{key}_max"].valueChanged.connect(lambda v, k=key: self._on_hsv_changed(k, "max", v))

        self.use_hsv_chk.toggled.connect(lambda v: setattr(self.chroma, "use_hsv", bool(v)))
        self.h_wrap_chk.toggled.connect(self._on_h_wrap_toggled)
        self.hsv_pick_btn.clicked.connect(self._fill_hsv_from_pick)
        self.feather_sld.valueChanged.connect(self._on_feather_changed)
        self.persist_chk.toggled.connect(lambda v: setattr(self.chroma, "persist", bool(v)))

        if self.owner is not None and hasattr(self.owner, "_on_feather"):
            self.vignette_sld.valueChanged.connect(self.owner._on_feather)
            self.vignette_sld.valueChanged.connect(lambda v: (self._update_vignette_label(), self._show_slider_tip(self.vignette_sld, "Мягкость виньетки", v)))
        else:
            self.vignette_sld.setEnabled(False)

        for _w in (self.layer_pipettes_chk, self.layer_crop_chk,
                   self.layer_circle_chk, self.layer_dim_chk):
            _w.toggled.connect(self._on_preview_layer_toggled)
        self.preview_mirror_chk.toggled.connect(self._on_preview_mirror_toggled)

        self.mode_orig_rb.toggled.connect(lambda v: v and self._set_preview_mode("orig"))
        self.mode_result_rb.toggled.connect(lambda v: v and self._set_preview_mode("result"))
        self.mode_mask_rb.toggled.connect(lambda v: v and self._set_preview_mode("mask"))

        self.vignette_on_top_chk.toggled.connect(self._on_vignette_on_top)
        self.vignette_click_through_chk.toggled.connect(self._on_vignette_click_through)
        self.vignette_mirror_chk.toggled.connect(self._on_vignette_mirror)
        self.vignette_opacity_sld.valueChanged.connect(self._on_vignette_opacity)

        self.crop_enabled_chk.toggled.connect(self._on_crop_enabled)
        self.crop_off_rb.toggled.connect(lambda v: v and self._on_crop_mode_selected("off"))
        self.crop_manual_rb.toggled.connect(lambda v: v and self._on_crop_mode_selected("manual"))
        self.crop_dynamic_rb.toggled.connect(lambda v: v and self._on_crop_mode_selected("dynamic"))
        self.crop_reset_btn.clicked.connect(self._reset_crop)
        self.crop_capture_btn.clicked.connect(self._capture_full_frame_crop)
        for _w in self._dynamic_setting_sliders:
            _w.valueChanged.connect(self._on_dynamic_setting_changed)
        self.dynamic_tracking_mode_combo.currentIndexChanged.connect(self._on_dynamic_setting_changed)
        self.dynamic_detector_combo.currentIndexChanged.connect(self._on_dynamic_setting_changed)
        for _w in (self.dynamic_arrows_move_face_chk, self.dynamic_invert_x_chk, self.dynamic_invert_y_chk):
            _w.toggled.connect(self._on_dynamic_setting_changed)
        self.dynamic_auto_center_btn.clicked.connect(self._on_dynamic_auto_center)
        self.dynamic_capture_btn.clicked.connect(self._on_dynamic_capture_current)
        self.dynamic_reset_params_btn.clicked.connect(self._on_dynamic_reset_params)

        for _w in self._ptz_setting_sliders:
            _w.valueChanged.connect(self._on_ptz_setting_changed)
        for _w in self._ptz_position_sliders:
            _w.valueChanged.connect(self._on_ptz_position_slider_changed)
        for _w in (self.ptz_enabled_chk, self.ptz_edge_guard_chk, self.ptz_focus_thirds_chk,
                   self.ptz_invert_pan_chk, self.ptz_invert_tilt_chk, self.ptz_invert_zoom_chk,
                   self.ptz_show_debug_chk):
            _w.toggled.connect(self._on_ptz_setting_changed)
        self.ptz_left_btn.clicked.connect(lambda: self._ptz_manual("pan", -1))
        self.ptz_right_btn.clicked.connect(lambda: self._ptz_manual("pan", 1))
        self.ptz_up_btn.clicked.connect(lambda: self._ptz_manual("tilt", -1))
        self.ptz_down_btn.clicked.connect(lambda: self._ptz_manual("tilt", 1))
        self.ptz_zoom_in_btn.clicked.connect(lambda: self._ptz_manual("zoom", 1))
        self.ptz_zoom_out_btn.clicked.connect(lambda: self._ptz_manual("zoom", -1))
        self.ptz_phys_left_btn.clicked.connect(lambda: self._ptz_manual_physical("pan", -1))
        self.ptz_phys_right_btn.clicked.connect(lambda: self._ptz_manual_physical("pan", 1))
        self.ptz_phys_up_btn.clicked.connect(lambda: self._ptz_manual_physical("tilt", -1))
        self.ptz_phys_down_btn.clicked.connect(lambda: self._ptz_manual_physical("tilt", 1))
        self.ptz_read_position_btn.clicked.connect(lambda: self._sync_ptz_position_sliders(read_camera=True))
        self.ptz_remember_home_btn.clicked.connect(self._ptz_remember_home)
        self.ptz_return_home_btn.clicked.connect(self._ptz_return_home)

        self.vcam_enabled_chk.toggled.connect(self._on_vcam_enabled)
        self.vcam_mirror_chk.toggled.connect(self._on_vcam_mirror)
        self.vcam_native_chk.toggled.connect(self._on_vcam_native)
        self.vcam_circle_overlay_chk.toggled.connect(self._on_vcam_circle_overlay)
        self.vcam_scale_sld.valueChanged.connect(self._on_vcam_scale)
        self.vcam_vignette_size_sld.valueChanged.connect(self._on_vcam_vignette_size)
        self.vcam_mode_combo.currentIndexChanged.connect(self._on_vcam_mode_combo)
        self.vcam_bg_load_btn.clicked.connect(self._on_vcam_load_bg)
        self.vcam_bg_telemost_btn.clicked.connect(self._on_vcam_telemost_bg)
        self.vcam_bg_clear_btn.clicked.connect(self._on_vcam_clear_bg)
        self.vcam_avatar_bg_color_btn.clicked.connect(self._on_vcam_avatar_bg_color)
        self.vcam_cx_spin.valueChanged.connect(lambda v: setattr(self.owner.state, "vcam_circle_x", int(v)))
        self.vcam_cy_spin.valueChanged.connect(lambda v: setattr(self.owner.state, "vcam_circle_y", int(v)))
        self.vcam_cr_sld.valueChanged.connect(self._on_vcam_circle_r_changed)
        self.vcam_cr_spin.valueChanged.connect(self._on_vcam_circle_r_changed)

        self.reset_btn.clicked.connect(self._reset_chroma_settings)
        self.close_btn.clicked.connect(self.close)

        self._load_from_model()
        self._load_vcam_from_owner()
        self._update_crop_label()
        self._update_camera_status()
        self._update_vcam_status()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._render_all_previews)
        self._timer.start(1000 // 15)

    # ------------------------------------------------------------------
    # Панели UI
    # ------------------------------------------------------------------
    def _scroll_area(self, widget: QWidget) -> QtWidgets.QScrollArea:
        area = QtWidgets.QScrollArea(self)
        area.setWidgetResizable(True)
        area.setFrameShape(QtWidgets.QFrame.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        area.setWidget(widget)
        return area

    def _tab_page(self, *widgets: QWidget) -> QtWidgets.QScrollArea:
        page = QWidget(self)
        lay = QVBoxLayout(page)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)
        for widget in widgets:
            lay.addWidget(widget)
        lay.addStretch(1)
        return self._scroll_area(page)

    def _build_chroma_panel(self) -> QGroupBox:
        box = QGroupBox("Хромакей")
        root = QVBoxLayout(box)
        root.setSpacing(7)
        root.addWidget(self.enabled_chk)

        slots_widget = QWidget(box)
        sl = QGridLayout(slots_widget)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setHorizontalSpacing(6)
        sl.setVerticalSpacing(5)
        for i, (chk, pick_btn, swatch, rgb_lbl, tol_sld, _tol_spin) in enumerate(self._slot_widgets):
            row = i
            tol_sld.setToolTip(f"Допуск {self.PICK_LABELS[i]}: {tol_sld.value()}")
            sl.addWidget(chk, row, 0)
            sl.addWidget(pick_btn, row, 1)
            sl.addWidget(swatch, row, 2)
            sl.addWidget(rgb_lbl, row, 3)
            sl.addWidget(tol_sld, row, 4)
        feather_row = len(self._slot_widgets)
        sl.addWidget(self.feather_lbl, feather_row, 1, 1, 3)
        sl.addWidget(self.feather_sld, feather_row, 4)
        sl.setColumnStretch(4, 1)
        root.addWidget(slots_widget)

        hsv_box = QGroupBox("HSV")
        hl = QGridLayout(hsv_box)
        hl.addWidget(self.use_hsv_chk, 0, 0, 1, 2)
        hl.addWidget(self.h_wrap_chk, 0, 2, 1, 2)
        for row_idx, (label, key, _lo, _hi) in enumerate(self._hsv_fields, 1):
            hl.addWidget(QLabel(f"{label} min"), row_idx, 0)
            hl.addWidget(self._hsv_sliders[f"{key}_min"], row_idx, 1)
            hl.addWidget(QLabel(f"{label} max"), row_idx, 2)
            hl.addWidget(self._hsv_sliders[f"{key}_max"], row_idx, 3)
        hl.addWidget(self.hsv_pick_btn, len(self._hsv_fields) + 1, 0, 1, 4)
        hl.setColumnStretch(1, 1)
        hl.setColumnStretch(3, 1)
        root.addWidget(hsv_box)
        root.addStretch(1)
        return box

    def _build_vignette_panel(self) -> QGroupBox:
        box = QGroupBox("Виньетка")
        root = QGridLayout(box)
        root.addWidget(self.vignette_on_top_chk, 0, 0)
        root.addWidget(self.vignette_click_through_chk, 0, 1)
        root.addWidget(self.vignette_mirror_chk, 0, 2)
        root.addWidget(self.vignette_lbl, 1, 0)
        root.addWidget(self.vignette_sld, 1, 1)
        root.addWidget(self.vignette_opacity_lbl, 1, 2)
        root.addWidget(self.vignette_opacity_sld, 1, 3)
        root.setColumnStretch(1, 1)
        root.setColumnStretch(3, 1)
        return box

    def _add_dynamic_slider_row(self, layout: QGridLayout, row: int,
                                label: str, slider: QSlider,
                                value_label: QLabel, tip: str = ""):
        lbl = QLabel(label)
        if tip:
            lbl.setToolTip(tip)
            slider.setToolTip(tip)
            value_label.setToolTip(tip)
        layout.addWidget(lbl, row, 0)
        layout.addWidget(slider, row, 1)
        layout.addWidget(value_label, row, 2)
        layout.setColumnStretch(1, 1)

    def _dynamic_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#dfe7ef; font-weight:600; padding-top:6px;")
        return lbl

    def _build_crop_panel(self) -> QGroupBox:
        box = QGroupBox("Кроп")
        root = QGridLayout(box)
        root.setHorizontalSpacing(8)
        root.setVerticalSpacing(6)

        mode_row = QWidget(box)
        mode_lay = QHBoxLayout(mode_row)
        mode_lay.setContentsMargins(0, 0, 0, 0)
        mode_lay.setSpacing(14)
        mode_lay.addWidget(self.crop_off_rb)
        mode_lay.addWidget(self.crop_manual_rb)
        mode_lay.addWidget(self.crop_dynamic_rb)
        mode_lay.addStretch(1)

        dynamic_box = QGroupBox("Динамический кроп")
        dl = QGridLayout(dynamic_box)
        dl.setHorizontalSpacing(8)
        dl.setVerticalSpacing(4)
        row = 0

        dl.addWidget(self._dynamic_header("Композиция"), row, 0, 1, 3); row += 1
        self._add_dynamic_slider_row(dl, row, "Диаметр круга", self.dynamic_circle_sld, self.dynamic_circle_val_lbl, "Диаметр круга относительно габарита лица."); row += 1
        self._add_dynamic_slider_row(dl, row, "Положение круга X", self.dynamic_circle_x_sld, self.dynamic_circle_x_val_lbl, "Смещение всего композиционного круга по X."); row += 1
        self._add_dynamic_slider_row(dl, row, "Положение круга Y", self.dynamic_circle_y_sld, self.dynamic_circle_y_val_lbl, "Смещение всего композиционного круга по Y."); row += 1

        dl.addWidget(self._dynamic_header("Лицо внутри круга"), row, 0, 1, 3); row += 1
        self._add_dynamic_slider_row(dl, row, "Лицо X", self.dynamic_face_x_sld, self.dynamic_face_x_val_lbl, "Положение лица внутри круга по X. То же смещение меняют стрелки."); row += 1
        self._add_dynamic_slider_row(dl, row, "Лицо Y", self.dynamic_face_y_sld, self.dynamic_face_y_val_lbl, "Положение лица внутри круга по Y. То же смещение меняют стрелки."); row += 1
        self._add_dynamic_slider_row(dl, row, "Запас вокруг лица", self.dynamic_padding_sld, self.dynamic_padding_val_lbl, "Дополнительный запас кадра вокруг композиционного круга."); row += 1

        dl.addWidget(self._dynamic_header("Движение"), row, 0, 1, 3); row += 1
        self._add_dynamic_slider_row(dl, row, "Плавность позиции", self.dynamic_smoothing_sld, self.dynamic_smoothing_val_lbl, "Сглаживание X/Y. Больше — быстрее догоняет положение, меньше — спокойнее."); row += 1
        self._add_dynamic_slider_row(dl, row, "Плавность масштаба", self.dynamic_scale_smoothing_sld, self.dynamic_scale_smoothing_val_lbl, "Сглаживание диаметра круга. Меньше — меньше дыхания зума."); row += 1
        self._add_dynamic_slider_row(dl, row, "Скорость возврата", self.dynamic_return_speed_sld, self.dynamic_return_speed_val_lbl, "Плавный возврат к центру, если лицо потеряно. По умолчанию выключен, чтобы кроп не дёргался."); row += 1
        self._add_dynamic_slider_row(dl, row, "Порог позиции", self.dynamic_center_dead_zone_sld, self.dynamic_center_dead_zone_val_lbl, "Мёртвая зона для X/Y. Чем больше, тем спокойнее позиция."); row += 1
        self._add_dynamic_slider_row(dl, row, "Порог масштаба", self.dynamic_scale_dead_zone_sld, self.dynamic_scale_dead_zone_val_lbl, "Мёртвая зона для изменения диаметра. Чем больше, тем меньше паразитный зум."); row += 1
        self._add_dynamic_slider_row(dl, row, "Макс. смещение", self.dynamic_max_offset_sld, self.dynamic_max_offset_val_lbl, "Ограничение ручного смещения лица и круга."); row += 1

        dl.addWidget(self._dynamic_header("Детекция"), row, 0, 1, 3); row += 1
        dl.addWidget(QLabel("Режим цели"), row, 0)
        dl.addWidget(self.dynamic_tracking_mode_combo, row, 1, 1, 2); row += 1
        dl.addWidget(QLabel("Детектор"), row, 0)
        dl.addWidget(self.dynamic_detector_combo, row, 1, 1, 2); row += 1
        self._add_dynamic_slider_row(dl, row, "Анализ кадра", self.dynamic_analysis_sld, self.dynamic_analysis_val_lbl, "Процент исходного кадра для детектора лица."); row += 1
        self._add_dynamic_slider_row(dl, row, "Мин. лицо", self.dynamic_min_face_sld, self.dynamic_min_face_val_lbl, "Минимальный размер лица в исходном кадре."); row += 1
        self._add_dynamic_slider_row(dl, row, "Панель виньетки", self.dynamic_panel_width_sld, self.dynamic_panel_width_val_lbl, "Ширина будущей правой панели предпросмотра. Сейчас только сохраняется."); row += 1
        self._add_dynamic_slider_row(dl, row, "Шаг стрелок", self.dynamic_nudge_sld, self.dynamic_nudge_val_lbl, "Смещение за одно нажатие стрелки."); row += 1

        dl.addWidget(self._dynamic_header("Управление стрелками"), row, 0, 1, 3); row += 1
        dl.addWidget(self.dynamic_arrows_move_face_chk, row, 0, 1, 3); row += 1
        dl.addWidget(self.dynamic_invert_x_chk, row, 0, 1, 3); row += 1
        dl.addWidget(self.dynamic_invert_y_chk, row, 0, 1, 3); row += 1

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addWidget(self.dynamic_auto_center_btn)
        btn_row.addWidget(self.dynamic_capture_btn)
        btn_row.addWidget(self.dynamic_reset_params_btn)
        btn_row.addStretch(1)
        btn_widget = QWidget(dynamic_box)
        btn_widget.setLayout(btn_row)
        dl.addWidget(btn_widget, row, 0, 1, 3)

        root.addWidget(mode_row, 0, 0, 1, 2)
        root.addWidget(self.crop_rect_lbl, 1, 0, 1, 2)
        root.addWidget(dynamic_box, 2, 0, 1, 2)
        root.addWidget(self.crop_hint_lbl, 3, 0, 1, 2)
        root.addWidget(self.crop_capture_btn, 4, 0)
        root.addWidget(self.crop_reset_btn, 4, 1)
        return box

    def _add_ptz_slider_row(self, layout: QGridLayout, row: int,
                            label: str, slider: QSlider, value_label: QLabel, tip: str = ""):
        lbl = QLabel(label)
        if tip:
            lbl.setToolTip(tip)
            slider.setToolTip(tip)
            value_label.setToolTip(tip)
        layout.addWidget(lbl, row, 0)
        layout.addWidget(slider, row, 1)
        layout.addWidget(value_label, row, 2)
        layout.setColumnStretch(1, 1)

    def _build_ptz_panel(self) -> QGroupBox:
        box = QGroupBox("PTZ камера")
        root = QGridLayout(box)
        root.setHorizontalSpacing(8)
        root.setVerticalSpacing(6)
        row = 0

        root.addWidget(self.ptz_enabled_chk, row, 0, 1, 3); row += 1
        root.addWidget(self.ptz_edge_guard_chk, row, 0, 1, 3); row += 1
        root.addWidget(self.ptz_focus_thirds_chk, row, 0, 1, 3); row += 1

        root.addWidget(self._dynamic_header("Положение камеры"), row, 0, 1, 3); row += 1
        self._add_ptz_slider_row(root, row, "Pan позиция", self.ptz_pan_pos_sld, self.ptz_pan_pos_val_lbl, "Абсолютная команда CAP_PROP_PAN. Ползунок всегда двигает физическую камеру, даже если включён динамический кроп."); row += 1
        self._add_ptz_slider_row(root, row, "Tilt позиция", self.ptz_tilt_pos_sld, self.ptz_tilt_pos_val_lbl, "Абсолютная команда CAP_PROP_TILT. Ползунок показывает последнее считанное или отправленное положение."); row += 1
        self._add_ptz_slider_row(root, row, "Zoom позиция", self.ptz_zoom_pos_sld, self.ptz_zoom_pos_val_lbl, "Абсолютная команда CAP_PROP_ZOOM. Диапазон условный: разные драйверы трактуют его по-своему."); row += 1

        root.addWidget(self._dynamic_header("Триггеры"), row, 0, 1, 3); row += 1
        self._add_ptz_slider_row(root, row, "Запас края", self.ptz_edge_guard_sld, self.ptz_edge_guard_val_lbl, "Процент от ширины/высоты кадра. Если динамический кроп подходит к этой зоне, камера подруливает физически."); row += 1
        self._add_ptz_slider_row(root, row, "Верх/низ экрана", self.ptz_focus_third_sld, self.ptz_focus_third_val_lbl, "Граница верхней и нижней зоны для фокусной точки. 33% = последние трети сверху и снизу."); row += 1
        self._add_ptz_slider_row(root, row, "Пауза команд", self.ptz_cooldown_sld, self.ptz_cooldown_val_lbl, "Минимальная пауза между PTZ-командами в кадрах, чтобы камера не получала очередь из команд."); row += 1

        root.addWidget(self._dynamic_header("Шаги PTZ"), row, 0, 1, 3); row += 1
        self._add_ptz_slider_row(root, row, "Pan", self.ptz_pan_step_sld, self.ptz_pan_step_val_lbl, "Шаг физического поворота по горизонтали через CAP_PROP_PAN."); row += 1
        self._add_ptz_slider_row(root, row, "Tilt", self.ptz_tilt_step_sld, self.ptz_tilt_step_val_lbl, "Шаг физического наклона через CAP_PROP_TILT."); row += 1
        self._add_ptz_slider_row(root, row, "Zoom", self.ptz_zoom_step_sld, self.ptz_zoom_step_val_lbl, "Шаг физического зума через CAP_PROP_ZOOM. Сейчас используется только ручными кнопками."); row += 1

        inv_row = QWidget(box)
        inv_lay = QHBoxLayout(inv_row)
        inv_lay.setContentsMargins(0, 0, 0, 0)
        inv_lay.addWidget(self.ptz_invert_pan_chk)
        inv_lay.addWidget(self.ptz_invert_tilt_chk)
        inv_lay.addWidget(self.ptz_invert_zoom_chk)
        inv_lay.addWidget(self.ptz_show_debug_chk)
        inv_lay.addStretch(1)
        root.addWidget(inv_row, row, 0, 1, 3); row += 1

        btn_row = QWidget(box)
        btn_lay = QHBoxLayout(btn_row)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        for btn in (self.ptz_left_btn, self.ptz_right_btn, self.ptz_up_btn, self.ptz_down_btn, self.ptz_zoom_in_btn, self.ptz_zoom_out_btn):
            btn_lay.addWidget(btn)
        btn_lay.addStretch(1)
        root.addWidget(btn_row, row, 0, 1, 3); row += 1

        phys_row = QWidget(box)
        phys_lay = QHBoxLayout(phys_row)
        phys_lay.setContentsMargins(0, 0, 0, 0)
        phys_lay.addWidget(QLabel("Физический тест:"))
        for btn in (self.ptz_phys_left_btn, self.ptz_phys_right_btn, self.ptz_phys_up_btn, self.ptz_phys_down_btn):
            phys_lay.addWidget(btn)
        phys_lay.addWidget(self.ptz_read_position_btn)
        phys_lay.addStretch(1)
        root.addWidget(phys_row, row, 0, 1, 3); row += 1

        home_row = QWidget(box)
        home_lay = QHBoxLayout(home_row)
        home_lay.setContentsMargins(0, 0, 0, 0)
        home_lay.addWidget(self.ptz_remember_home_btn)
        home_lay.addWidget(self.ptz_return_home_btn)
        home_lay.addStretch(1)
        root.addWidget(home_row, row, 0, 1, 3); row += 1

        root.addWidget(self.ptz_status_lbl, row, 0, 1, 3)
        return box

    def _build_vcam_panel(self) -> QGroupBox:
        box = QGroupBox("Виртуальная камера")
        root = QGridLayout(box)
        row = 0
        root.addWidget(self.vcam_enabled_chk, row, 0, 1, 2)
        root.addWidget(self.vcam_mirror_chk, row, 2, 1, 2)
        row += 1
        root.addWidget(self.vcam_native_chk, row, 0, 1, 4)
        row += 1
        root.addWidget(self.vcam_circle_overlay_chk, row, 0, 1, 4)
        row += 1
        root.addWidget(QLabel("Режим вывода"), row, 0)
        root.addWidget(self.vcam_mode_combo, row, 1, 1, 3)
        row += 1
        root.addWidget(QLabel("Фон / подложка"), row, 0)
        root.addWidget(self.vcam_bg_load_btn, row, 1)
        root.addWidget(self.vcam_bg_telemost_btn, row, 2)
        root.addWidget(self.vcam_bg_clear_btn, row, 3)
        row += 1
        root.addWidget(self.vcam_bg_path_lbl, row, 0, 1, 4)
        row += 1
        root.addWidget(QLabel("Фон аватарки"), row, 0)
        root.addWidget(self.vcam_avatar_bg_lbl, row, 1, 1, 2)
        root.addWidget(self.vcam_avatar_bg_color_btn, row, 3)
        row += 1
        root.addWidget(QLabel("Круг X"), row, 0)
        root.addWidget(self.vcam_cx_spin, row, 1)
        root.addWidget(QLabel("Y"), row, 2)
        root.addWidget(self.vcam_cy_spin, row, 3)
        row += 1
        root.addWidget(QLabel("R"), row, 0)
        self.vcam_cr_sld.setToolTip(f"R: {self.vcam_cr_sld.value()}")
        root.addWidget(self.vcam_cr_sld, row, 1, 1, 3)
        root.setColumnStretch(3, 1)
        return box

    # ------------------------------------------------------------------
    # Камеры
    # ------------------------------------------------------------------
    def _reload_camera_combo(self):
        if self.owner is None:
            return
        self.camera_combo.blockSignals(True)
        self.camera_combo.clear()
        for idx in sorted(set(getattr(self.owner, "available_cameras", [self.owner.camera_index]))):
            self.camera_combo.addItem(self._camera_title(idx), idx)
        pos = self.camera_combo.findData(self.owner.camera_index)
        if pos >= 0:
            self.camera_combo.setCurrentIndex(pos)
        self.camera_combo.blockSignals(False)

    def _camera_title(self, idx: int) -> str:
        if self.owner is None:
            return f"Камера {idx}"
        if hasattr(self.owner, "camera_display_name"):
            return self.owner.camera_display_name(idx, include_props=(idx == getattr(self.owner, "camera_index", -1)))
        return f"Камера {idx}"

    def _on_camera_rename(self):
        if self.owner is None:
            return
        idx = self.camera_combo.currentData()
        if idx is None:
            return
        idx = int(idx)
        aliases = getattr(self.owner.state, "camera_aliases", None)
        if not isinstance(aliases, dict):
            aliases = {}
            self.owner.state.camera_aliases = aliases
        current = str(aliases.get(str(idx), ""))
        fallback = self.owner.camera_display_name(idx, include_props=False) if hasattr(self.owner, "camera_display_name") else f"Камера {idx}"
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Переименовать камеру",
            f"Название для камеры {idx}:",
            QtWidgets.QLineEdit.Normal,
            current or fallback,
        )
        if not ok:
            return
        name = text.strip()
        if name:
            aliases[str(idx)] = name
        else:
            aliases.pop(str(idx), None)
        if self.owner.chroma.persist:
            self.owner.save_config()
        if hasattr(self.owner, "refresh_camera_labels"):
            self.owner.refresh_camera_labels()
        self._reload_camera_combo()
        self._update_camera_status()

    def _on_camera_combo_changed(self, _idx: int):
        if self.owner is None:
            return
        cam_idx = self.camera_combo.currentData()
        if cam_idx is None or int(cam_idx) == self.owner.camera_index:
            return
        self.owner.switch_camera(int(cam_idx))
        self._reload_camera_combo()
        self._update_camera_status()

    def _on_camera_refresh(self):
        if self.owner is None:
            return
        self.owner.refresh_cameras()
        self._reload_camera_combo()
        self._update_camera_status()

    def _update_camera_status(self):
        if self.owner is None:
            self.camera_status_lbl.setText("")
            return
        cap = getattr(self.owner, "cap", None)
        if cap is not None and cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            fps = int(round(cap.get(cv2.CAP_PROP_FPS) or (self.owner.fps or 30)))
            name = self.owner.camera_display_name(self.owner.camera_index, include_props=False) if hasattr(self.owner, "camera_display_name") else f"Камера {self.owner.camera_index}"
            self.camera_status_lbl.setText(f"{name} · {w}×{h} · {fps} FPS")
        else:
            self.camera_status_lbl.setText("Камера выключена")

    # ------------------------------------------------------------------
    # Загрузка модели
    # ------------------------------------------------------------------
    def _load_from_model(self):
        c = self.chroma
        self.enabled_chk.blockSignals(True)
        self.enabled_chk.setChecked(bool(c.enabled))
        self.enabled_chk.blockSignals(False)

        for i, slot in enumerate(c.picks):
            chk, _pick_btn, _swatch, _rgb_lbl, tol_sld, tol_spin = self._slot_widgets[i]
            for w in (chk, tol_sld, tol_spin):
                w.blockSignals(True)
            chk.setChecked(bool(slot.enabled))
            tol_sld.setValue(int(slot.tol))
            tol_spin.setValue(int(slot.tol))
            for w in (chk, tol_sld, tol_spin):
                w.blockSignals(False)
            self._refresh_slot_visual(i)

        self.use_hsv_chk.blockSignals(True)
        self.use_hsv_chk.setChecked(bool(c.use_hsv))
        self.use_hsv_chk.blockSignals(False)
        self.h_wrap_chk.blockSignals(True)
        self.h_wrap_chk.setChecked(bool(c.h_wrap))
        self.h_wrap_chk.blockSignals(False)

        for key in ("h", "s", "v"):
            for end_name in ("min", "max"):
                value = int(getattr(c, f"{key}_{end_name}"))
                for w in (self._hsv_sliders[f"{key}_{end_name}"], self._hsv_spins[f"{key}_{end_name}"]):
                    w.blockSignals(True)
                    w.setValue(value)
                    w.blockSignals(False)

        self.feather_sld.blockSignals(True)
        self.feather_sld.setValue(int(c.feather))
        self.feather_sld.blockSignals(False)
        self.persist_chk.blockSignals(True)
        self.persist_chk.setChecked(bool(c.persist))
        self.persist_chk.blockSignals(False)

        if self.owner is not None:
            self.vignette_sld.blockSignals(True)
            self.vignette_sld.setValue(int(self.owner.state.edge_feather))
            self.vignette_sld.blockSignals(False)
            for _widget, _attr in ((self.layer_pipettes_chk, "preview_show_pipettes"),
                                   (self.layer_crop_chk, "preview_show_crop"),
                                   (self.layer_circle_chk, "preview_show_circle"),
                                   (self.layer_dim_chk, "preview_show_dimming"),
                                   (self.preview_mirror_chk, "preview_mirror")):
                _widget.blockSignals(True)
                _widget.setChecked(bool(getattr(self.owner.state, _attr, True)))
                _widget.blockSignals(False)
            self._sync_crop_mode_radios()
            self._load_dynamic_from_owner()
            self._load_ptz_from_owner()
            self._load_vignette_from_owner()

        self._update_feather_label()
        self._update_vignette_label()
        self._update_crop_label()

    def _load_ptz_from_owner(self):
        if self.owner is None:
            return
        cfg = getattr(self.owner, "ptz", PTZConfig())
        pairs = (
            (self.ptz_enabled_chk, bool(getattr(cfg, "enabled", False))),
            (self.ptz_edge_guard_chk, bool(getattr(cfg, "trigger_edge_guard", True))),
            (self.ptz_focus_thirds_chk, bool(getattr(cfg, "trigger_focus_vertical_thirds", True))),
            (self.ptz_invert_pan_chk, bool(getattr(cfg, "invert_pan", False))),
            (self.ptz_invert_tilt_chk, bool(getattr(cfg, "invert_tilt", False))),
            (self.ptz_invert_zoom_chk, bool(getattr(cfg, "invert_zoom", False))),
            (self.ptz_show_debug_chk, bool(getattr(cfg, "show_debug", False))),
        )
        for widget, value in pairs:
            widget.blockSignals(True)
            widget.setChecked(value)
            widget.blockSignals(False)
        self._set_slider_quiet(self.ptz_edge_guard_sld, int(getattr(cfg, "edge_guard_percent", 10)))
        self._set_slider_quiet(self.ptz_focus_third_sld, int(getattr(cfg, "focus_third_percent", 33)))
        self._set_slider_quiet(self.ptz_cooldown_sld, int(getattr(cfg, "cooldown_frames", 8)))
        self._set_slider_quiet(self.ptz_pan_step_sld, int(round(float(getattr(cfg, "pan_step", 1.0)) * 10)))
        self._set_slider_quiet(self.ptz_tilt_step_sld, int(round(float(getattr(cfg, "tilt_step", 1.0)) * 10)))
        self._set_slider_quiet(self.ptz_zoom_step_sld, int(round(float(getattr(cfg, "zoom_step", 1.0)) * 10)))
        self._sync_ptz_position_sliders(read_camera=False)
        self._update_ptz_slider_labels()
        self._update_ptz_status()

    def _update_ptz_slider_labels(self):
        self.ptz_edge_guard_val_lbl.setText(f"{self.ptz_edge_guard_sld.value()}%")
        self.ptz_focus_third_val_lbl.setText(f"{self.ptz_focus_third_sld.value()}%")
        self.ptz_cooldown_val_lbl.setText(f"{self.ptz_cooldown_sld.value()} кадр.")
        self.ptz_pan_step_val_lbl.setText(f"{self.ptz_pan_step_sld.value() / 10:.1f}")
        self.ptz_tilt_step_val_lbl.setText(f"{self.ptz_tilt_step_sld.value() / 10:.1f}")
        self.ptz_zoom_step_val_lbl.setText(f"{self.ptz_zoom_step_sld.value() / 10:.1f}")
        self._update_ptz_position_labels()

    def _ptz_position_value_from_slider(self, slider: QSlider) -> float:
        return float(slider.value()) / 10.0

    def _ptz_position_axis_widgets(self, axis: str):
        if axis == "pan":
            return self.ptz_pan_pos_sld, self.ptz_pan_pos_val_lbl
        if axis == "tilt":
            return self.ptz_tilt_pos_sld, self.ptz_tilt_pos_val_lbl
        return self.ptz_zoom_pos_sld, self.ptz_zoom_pos_val_lbl

    def _ptz_axis_display_value(self, axis: str, read_camera: bool = False) -> float:
        if self.owner is None:
            return 0.0
        runtime = getattr(self.owner, "_ptz_runtime", PTZRuntimeState())
        value = None
        if read_camera and hasattr(self.owner, "_ptz_read_axis"):
            value = self.owner._ptz_read_axis(axis)
        if value is None:
            command_value = getattr(runtime, f"command_{axis}", None)
            if command_value is not None:
                value = command_value
        if value is None:
            last_value = getattr(runtime, f"last_{axis}", None)
            if last_value is not None:
                value = last_value
        if value is None:
            value = 0.0
        try:
            return float(value)
        except Exception:
            return 0.0

    def _sync_ptz_position_sliders(self, read_camera: bool = False):
        """Синхронизирует ползунки физического положения PTZ.

        Важная оговорка: OpenCV/DirectShow часто не отдаёт реальное положение
        Pan/Tilt/Zoom. Поэтому ползунок показывает лучшее доступное значение:
        сначала последнее отправленное командное значение, а при нажатии
        «Считать из камеры» — то, что вернул драйвер. Да, драйверы снова
        делают вид, что это не их проблема.
        """
        for axis in ("pan", "tilt", "zoom"):
            slider, _label = self._ptz_position_axis_widgets(axis)
            value = self._ptz_axis_display_value(axis, read_camera=read_camera)
            self._set_slider_quiet(slider, int(round(float(value) * 10.0)))
        self._update_ptz_position_labels()
        self._update_ptz_status()

    def _update_ptz_position_labels(self):
        self.ptz_pan_pos_val_lbl.setText(f"{self._ptz_position_value_from_slider(self.ptz_pan_pos_sld):+.1f}")
        self.ptz_tilt_pos_val_lbl.setText(f"{self._ptz_position_value_from_slider(self.ptz_tilt_pos_sld):+.1f}")
        self.ptz_zoom_pos_val_lbl.setText(f"{self._ptz_position_value_from_slider(self.ptz_zoom_pos_sld):.1f}")

    def _on_ptz_position_slider_changed(self, _value=None):
        if self.owner is None:
            return
        sender = self.sender()
        axis = None
        if sender is self.ptz_pan_pos_sld:
            axis = "pan"
        elif sender is self.ptz_tilt_pos_sld:
            axis = "tilt"
        elif sender is self.ptz_zoom_pos_sld:
            axis = "zoom"
        if axis is None:
            self._update_ptz_position_labels()
            return
        slider, _label = self._ptz_position_axis_widgets(axis)
        value = self._ptz_position_value_from_slider(slider)
        ok = self.owner._ptz_set_axis_absolute(axis, value, reason="slider")
        self._update_ptz_position_labels()
        self._update_ptz_status()
        if not ok:
            # Не показываем QMessageBox на каждом пикселе движения ползунка.
            # Сообщение видно в строке статуса PTZ. Иначе UI сам станет PTZ: Постоянно Тормозящее Зло.
            pass

    def _update_ptz_status(self):
        if self.owner is None:
            self.ptz_status_lbl.setText("")
            return
        runtime = getattr(self.owner, "_ptz_runtime", PTZRuntimeState())
        cfg = getattr(self.owner, "ptz", PTZConfig())
        status = "включён" if bool(getattr(cfg, "enabled", False)) else "выключен"
        msg = getattr(runtime, "last_command", "") or getattr(runtime, "last_error", "")
        trig = getattr(runtime, "last_trigger", "")
        pos = (
            f"pan={self._ptz_axis_display_value('pan'):+.1f} · "
            f"tilt={self._ptz_axis_display_value('tilt'):+.1f} · "
            f"zoom={self._ptz_axis_display_value('zoom'):.1f}"
        )
        extra = msg or trig
        if extra:
            self.ptz_status_lbl.setText(f"PTZ: {status} · {pos} · {extra}")
        else:
            self.ptz_status_lbl.setText(f"PTZ: {status} · {pos}")

    def _on_ptz_setting_changed(self, _value=None):
        if self.owner is None:
            return
        cfg = getattr(self.owner, "ptz", None)
        if cfg is None:
            return
        cfg.enabled = bool(self.ptz_enabled_chk.isChecked())
        cfg.trigger_edge_guard = bool(self.ptz_edge_guard_chk.isChecked())
        cfg.trigger_focus_vertical_thirds = bool(self.ptz_focus_thirds_chk.isChecked())
        cfg.invert_pan = bool(self.ptz_invert_pan_chk.isChecked())
        cfg.invert_tilt = bool(self.ptz_invert_tilt_chk.isChecked())
        cfg.invert_zoom = bool(self.ptz_invert_zoom_chk.isChecked())
        cfg.show_debug = bool(self.ptz_show_debug_chk.isChecked())
        cfg.edge_guard_percent = int(self.ptz_edge_guard_sld.value())
        cfg.focus_third_percent = int(self.ptz_focus_third_sld.value())
        cfg.cooldown_frames = int(self.ptz_cooldown_sld.value())
        cfg.pan_step = float(self.ptz_pan_step_sld.value() / 10.0)
        cfg.tilt_step = float(self.ptz_tilt_step_sld.value() / 10.0)
        cfg.zoom_step = float(self.ptz_zoom_step_sld.value() / 10.0)
        self._update_ptz_slider_labels()
        self._update_ptz_status()
        if self.owner.chroma.persist and hasattr(self.owner, "save_config"):
            self.owner.save_config()

    def _ptz_manual(self, axis: str, direction: int):
        if self.owner is None:
            return
        ok = False
        # В режиме динамического кропа Pan/Tilt двигают композиционную цель,
        # а не мотор камеры. Иначе одна кнопка будет одновременно менять две
        # системы координат. Нелепость понятная, но нам она не нужна.
        if axis in ("pan", "tilt") and bool(getattr(self.owner.dynamic_crop, "enabled", False)):
            step = float(getattr(self.owner.dynamic_crop, "nudge_step", COMPOSITION_NUDGE_STEP))
            if axis == "pan":
                self.owner._dynamic_adjust_offset(float(direction) * step, 0.0)
            else:
                self.owner._dynamic_adjust_offset(0.0, float(direction) * step)
            self.owner._ptz_runtime.last_command = f"цель {axis} {direction:+d}"
            self.owner._ptz_runtime.last_error = ""
            ok = True
        elif axis == "pan":
            ok = self.owner._ptz_pan(int(direction), reason="manual")
        elif axis == "tilt":
            ok = self.owner._ptz_tilt(int(direction), reason="manual")
        elif axis == "zoom":
            ok = self.owner._ptz_zoom(int(direction), reason="manual")
        self._load_dynamic_from_owner()
        self._sync_ptz_position_sliders(read_camera=False)
        if not ok:
            QMessageBox.information(self, "PTZ", "Камера или драйвер не приняли команду PTZ через OpenCV. Это не ошибка КругоЗора: часть камер не отдаёт Pan/Tilt/Zoom через CAP_PROP.")

    def _ptz_manual_physical(self, axis: str, direction: int):
        """Всегда двигает физическую камеру, даже если динамический кроп включён."""
        if self.owner is None:
            return
        if axis == "pan":
            ok = self.owner._ptz_pan(int(direction), reason="manual physical")
        elif axis == "tilt":
            ok = self.owner._ptz_tilt(int(direction), reason="manual physical")
        elif axis == "zoom":
            ok = self.owner._ptz_zoom(int(direction), reason="manual physical")
        else:
            ok = False
        self._sync_ptz_position_sliders(read_camera=False)
        if not ok:
            QMessageBox.information(self, "PTZ", "Камера или драйвер не приняли физическую PTZ-команду через OpenCV. Проверьте драйвер/DirectShow-доступ к Pan/Tilt/Zoom.")

    def _ptz_remember_home(self):
        if self.owner is None:
            return
        self.owner._ptz_remember_home()
        self._update_ptz_status()

    def _ptz_return_home(self):
        if self.owner is None:
            return
        self.owner._reset_camera_and_target_to_home()
        self._load_dynamic_from_owner()
        self._sync_ptz_position_sliders(read_camera=False)

    def _load_vcam_from_owner(self):
        if self.owner is None:
            return
        st = self.owner.state
        pairs = ((self.vcam_enabled_chk, st.vcam_enabled),
                 (self.vcam_mirror_chk, st.vcam_mirror),
                 (self.vcam_native_chk, st.vcam_passthrough_native),
                 (self.vcam_circle_overlay_chk, st.vcam_circle_overlay),
                 (self.vcam_auto_chk, st.vcam_circle_auto))
        for w, val in pairs:
            w.blockSignals(True)
            w.setChecked(bool(val))
            w.blockSignals(False)

        self.vcam_scale_sld.blockSignals(True)
        self.vcam_scale_sld.setValue(int(clamp(st.vcam_scale, 50, 200)))
        self.vcam_scale_sld.blockSignals(False)
        self.vcam_vignette_size_sld.blockSignals(True)
        self.vcam_vignette_size_sld.setValue(int(clamp(getattr(st, "vcam_vignette_scale", 100), 50, 100)))
        self.vcam_vignette_size_sld.blockSignals(False)

        idx = self.vcam_mode_combo.findData(getattr(st, "vcam_mode", "passthrough"))
        if idx < 0:
            idx = 0
        self.vcam_mode_combo.blockSignals(True)
        self.vcam_mode_combo.setCurrentIndex(idx)
        self.vcam_mode_combo.blockSignals(False)

        for sp, value in ((self.vcam_cx_spin, st.vcam_circle_x),
                          (self.vcam_cy_spin, st.vcam_circle_y),
                          (self.vcam_cr_spin, max(1, st.vcam_circle_r)),
                          (self.vcam_cr_sld, max(1, st.vcam_circle_r))):
            sp.blockSignals(True)
            sp.setValue(int(value))
            sp.blockSignals(False)

        self._update_vcam_scale_label()
        self._update_vcam_vignette_size_label()
        self._update_vcam_bg_label()
        self._update_vcam_avatar_bg_label()
        self._update_vcam_native_dependents()
        if not HAVE_PYVIRTUALCAM:
            self.vcam_status_lbl.setText("pyvirtualcam не установлен")
            self.vcam_enabled_chk.setEnabled(False)
        self._update_vcam_status()

    def _set_slider_quiet(self, slider: QSlider, value: int):
        slider.blockSignals(True)
        slider.setValue(int(value))
        slider.blockSignals(False)

    def _load_dynamic_from_owner(self):
        if self.owner is None:
            return
        cfg = getattr(self.owner, "dynamic_crop", DynamicCropConfig())
        self._set_slider_quiet(self.dynamic_analysis_sld, int(getattr(cfg, "analysis_scale_percent", DEFAULT_ANALYSIS_SCALE_PERCENT)))
        self._set_slider_quiet(self.dynamic_smoothing_sld, int(round(float(getattr(cfg, "position_smoothing", getattr(cfg, "smoothing", DEFAULT_SMOOTHING))) * 100)))
        self._set_slider_quiet(self.dynamic_scale_smoothing_sld, int(round(float(getattr(cfg, "scale_smoothing", 0.22)) * 100)))
        self._set_slider_quiet(self.dynamic_circle_sld, int(round(float(getattr(cfg, "circle_to_head", DEFAULT_CIRCLE_MARGIN)) * 100)))
        self._set_slider_quiet(self.dynamic_circle_x_sld, int(round(float(getattr(cfg, "circle_offset_x", DEFAULT_DYNAMIC_CIRCLE_OFFSET_X)) * 100)))
        self._set_slider_quiet(self.dynamic_circle_y_sld, int(round(float(getattr(cfg, "circle_offset_y", DEFAULT_DYNAMIC_CIRCLE_OFFSET_Y)) * 100)))
        self._set_slider_quiet(self.dynamic_face_x_sld, int(round(float(getattr(cfg, "offset_x", 0.0)) * 100)))
        self._set_slider_quiet(self.dynamic_face_y_sld, int(round(float(getattr(cfg, "offset_y", -0.05)) * 100)))
        self._set_slider_quiet(self.dynamic_padding_sld, int(round(float(getattr(cfg, "crop_padding", DEFAULT_DYNAMIC_CROP_PADDING)) * 100)))
        self._set_slider_quiet(self.dynamic_return_speed_sld, int(round(float(getattr(cfg, "return_speed", DEFAULT_DYNAMIC_RETURN_SPEED)) * 100)))
        self._set_slider_quiet(self.dynamic_center_dead_zone_sld, int(round(float(getattr(cfg, "position_dead_zone", getattr(cfg, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE))) * 100)))
        self._set_slider_quiet(self.dynamic_scale_dead_zone_sld, int(round(float(getattr(cfg, "scale_dead_zone", 0.08)) * 100)))
        self._set_slider_quiet(self.dynamic_max_offset_sld, int(round(float(getattr(cfg, "max_composition_offset", MAX_COMPOSITION_OFFSET)) * 100)))
        self._set_slider_quiet(self.dynamic_min_face_sld, int(getattr(cfg, "min_face_size_full_frame", MIN_FACE_SIZE_FULL_FRAME)))
        self._set_slider_quiet(self.dynamic_panel_width_sld, int(getattr(cfg, "vignette_panel_width", VIGNETTE_PANEL_WIDTH)))
        self._set_slider_quiet(self.dynamic_nudge_sld, int(round(float(getattr(cfg, "nudge_step", COMPOSITION_NUDGE_STEP)) * 1000)))

        mode_idx = self.dynamic_tracking_mode_combo.findData(str(getattr(cfg, "tracking_mode", "eyes_ipd") or "eyes_ipd"))
        if mode_idx < 0:
            mode_idx = 0
        self.dynamic_tracking_mode_combo.blockSignals(True)
        self.dynamic_tracking_mode_combo.setCurrentIndex(mode_idx)
        self.dynamic_tracking_mode_combo.blockSignals(False)

        detector_idx = self.dynamic_detector_combo.findData(str(getattr(cfg, "detector", "mediapipe") or "mediapipe"))
        if detector_idx < 0:
            detector_idx = 0
        self.dynamic_detector_combo.blockSignals(True)
        self.dynamic_detector_combo.setCurrentIndex(detector_idx)
        self.dynamic_detector_combo.blockSignals(False)

        for widget, value in (
            (self.dynamic_arrows_move_face_chk, bool(getattr(cfg, "arrows_move_face", True))),
            (self.dynamic_invert_x_chk, bool(getattr(cfg, "invert_arrows_x", False))),
            (self.dynamic_invert_y_chk, bool(getattr(cfg, "invert_arrows_y", False))),
        ):
            widget.blockSignals(True)
            widget.setChecked(value)
            widget.blockSignals(False)
        self._update_dynamic_slider_labels()

    def _update_dynamic_slider_labels(self):
        values = {
            self.dynamic_circle_val_lbl: f"{self.dynamic_circle_sld.value() / 100:.2f}",
            self.dynamic_circle_x_val_lbl: f"{self.dynamic_circle_x_sld.value() / 100:+.2f}",
            self.dynamic_circle_y_val_lbl: f"{self.dynamic_circle_y_sld.value() / 100:+.2f}",
            self.dynamic_face_x_val_lbl: f"{self.dynamic_face_x_sld.value() / 100:+.2f}",
            self.dynamic_face_y_val_lbl: f"{self.dynamic_face_y_sld.value() / 100:+.2f}",
            self.dynamic_padding_val_lbl: f"{self.dynamic_padding_sld.value() / 100:.2f}",
            self.dynamic_smoothing_val_lbl: f"{self.dynamic_smoothing_sld.value() / 100:.2f}",
            self.dynamic_scale_smoothing_val_lbl: f"{self.dynamic_scale_smoothing_sld.value() / 100:.2f}",
            self.dynamic_return_speed_val_lbl: f"{self.dynamic_return_speed_sld.value() / 100:.2f}",
            self.dynamic_center_dead_zone_val_lbl: f"{self.dynamic_center_dead_zone_sld.value()}%",
            self.dynamic_scale_dead_zone_val_lbl: f"{self.dynamic_scale_dead_zone_sld.value()}%",
            self.dynamic_max_offset_val_lbl: f"{self.dynamic_max_offset_sld.value() / 100:.2f}",
            self.dynamic_analysis_val_lbl: f"{self.dynamic_analysis_sld.value()}%",
            self.dynamic_min_face_val_lbl: f"{self.dynamic_min_face_sld.value()} px",
            self.dynamic_panel_width_val_lbl: f"{self.dynamic_panel_width_sld.value()} px",
            self.dynamic_nudge_val_lbl: f"{self.dynamic_nudge_sld.value() / 1000:.3f}",
        }
        for lbl, text in values.items():
            lbl.setText(text)

    def _on_dynamic_setting_changed(self, _value=None):
        if self.owner is None:
            return
        cfg = getattr(self.owner, "dynamic_crop", None)
        if cfg is None:
            return
        old_analysis = int(getattr(cfg, "analysis_scale_percent", DEFAULT_ANALYSIS_SCALE_PERCENT))
        old_min_face = int(getattr(cfg, "min_face_size_full_frame", MIN_FACE_SIZE_FULL_FRAME))
        old_detector = str(getattr(cfg, "detector", "mediapipe") or "mediapipe")
        old_tracking_mode = str(getattr(cfg, "tracking_mode", "eyes_ipd") or "eyes_ipd")

        max_offset = self.dynamic_max_offset_sld.value() / 100.0
        cfg.circle_to_head = float(clamp(self.dynamic_circle_sld.value() / 100.0, DYNAMIC_CROP_MIN_CIRCLE_TO_HEAD, DYNAMIC_CROP_MAX_CIRCLE_TO_HEAD))
        cfg.circle_offset_x = float(clamp(self.dynamic_circle_x_sld.value() / 100.0, -max_offset, max_offset))
        cfg.circle_offset_y = float(clamp(self.dynamic_circle_y_sld.value() / 100.0, -max_offset, max_offset))
        cfg.offset_x = float(clamp(self.dynamic_face_x_sld.value() / 100.0, -max_offset, max_offset))
        cfg.offset_y = float(clamp(self.dynamic_face_y_sld.value() / 100.0, -max_offset, max_offset))
        cfg.crop_padding = float(clamp(self.dynamic_padding_sld.value() / 100.0, 1.0, 1.6))
        cfg.position_smoothing = float(clamp(self.dynamic_smoothing_sld.value() / 100.0, 0.0, 0.8))
        cfg.scale_smoothing = float(clamp(self.dynamic_scale_smoothing_sld.value() / 100.0, 0.0, 0.8))
        # Совместимость со старой схемой и fallback-кодом.
        cfg.smoothing = cfg.position_smoothing
        cfg.return_speed = float(clamp(self.dynamic_return_speed_sld.value() / 100.0, 0.0, 1.0))
        cfg.position_dead_zone = float(clamp(self.dynamic_center_dead_zone_sld.value() / 100.0, 0.0, 0.30))
        cfg.scale_dead_zone = float(clamp(self.dynamic_scale_dead_zone_sld.value() / 100.0, 0.0, 0.30))
        cfg.center_dead_zone = cfg.position_dead_zone
        cfg.max_composition_offset = float(max_offset)
        cfg.analysis_scale_percent = int(self.dynamic_analysis_sld.value())
        cfg.min_face_size_full_frame = int(self.dynamic_min_face_sld.value())
        cfg.vignette_panel_width = int(self.dynamic_panel_width_sld.value())
        cfg.nudge_step = float(clamp(self.dynamic_nudge_sld.value() / 1000.0, 0.001, 0.100))
        cfg.arrows_move_face = bool(self.dynamic_arrows_move_face_chk.isChecked())
        cfg.invert_arrows_x = bool(self.dynamic_invert_x_chk.isChecked())
        cfg.invert_arrows_y = bool(self.dynamic_invert_y_chk.isChecked())
        cfg.tracking_mode = str(self.dynamic_tracking_mode_combo.currentData() or "eyes_ipd")
        cfg.detector = str(self.dynamic_detector_combo.currentData() or "mediapipe")

        # Если ползунок максимального смещения ограничил текущие смещения — синхронизируем ручки.
        for slider, value in (
            (self.dynamic_circle_x_sld, cfg.circle_offset_x),
            (self.dynamic_circle_y_sld, cfg.circle_offset_y),
            (self.dynamic_face_x_sld, cfg.offset_x),
            (self.dynamic_face_y_sld, cfg.offset_y),
        ):
            wanted = int(round(float(value) * 100))
            if slider.value() != wanted:
                self._set_slider_quiet(slider, wanted)

        if (old_analysis != cfg.analysis_scale_percent or
                old_min_face != cfg.min_face_size_full_frame or
                old_detector != str(getattr(cfg, "detector", "mediapipe") or "mediapipe") or
                old_tracking_mode != str(getattr(cfg, "tracking_mode", "eyes_ipd") or "eyes_ipd")):
            if hasattr(self.owner, "_dynamic_crop_runtime"):
                self.owner._dynamic_crop_runtime = DynamicCropRuntimeState()
            if hasattr(self.owner, "_reset_face_director"):
                self.owner._reset_face_director()
        self._update_dynamic_slider_labels()
        self._update_crop_label()
        if self.owner.chroma.persist and hasattr(self.owner, "save_config"):
            self.owner.save_config()

    def _on_dynamic_auto_center(self):
        for slider, value in (
            (self.dynamic_circle_x_sld, 0),
            (self.dynamic_circle_y_sld, 0),
            (self.dynamic_face_x_sld, 0),
            (self.dynamic_face_y_sld, -5),
        ):
            slider.setValue(value)
        self._on_dynamic_setting_changed()

    def _on_dynamic_capture_current(self):
        if self.owner is None:
            return
        runtime = getattr(self.owner, "_dynamic_crop_runtime", None)
        face = getattr(runtime, "face", None)
        circle = getattr(runtime, "circle", None)
        if face is None or circle is None or face.size <= 1 or circle.diameter <= 1:
            QMessageBox.information(self, "Нет лица", "Сначала дождитесь захвата лица динамическим кропом.")
            return
        self.dynamic_circle_sld.setValue(int(round(clamp(circle.diameter / face.size, DYNAMIC_CROP_MIN_CIRCLE_TO_HEAD, DYNAMIC_CROP_MAX_CIRCLE_TO_HEAD) * 100)))
        self.dynamic_face_x_sld.setValue(int(round(clamp((face.cx - circle.cx) / circle.diameter, -1.0, 1.0) * 100)))
        self.dynamic_face_y_sld.setValue(int(round(clamp((face.cy - circle.cy) / circle.diameter, -1.0, 1.0) * 100)))
        self._on_dynamic_setting_changed()

    def _on_dynamic_reset_params(self):
        if self.owner is None:
            return
        was_enabled = bool(getattr(self.owner.dynamic_crop, "enabled", False))
        self.owner.dynamic_crop = DynamicCropConfig(enabled=was_enabled)
        self.owner._dynamic_crop_runtime = DynamicCropRuntimeState()
        if hasattr(self.owner, "_reset_face_director"):
            self.owner._reset_face_director()
        self._sync_crop_mode_radios()
        self._load_dynamic_from_owner()
        self._update_crop_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    # ------------------------------------------------------------------
    # Хромакей
    # ------------------------------------------------------------------
    def _refresh_slot_visual(self, idx: int):
        slot = self.chroma.picks[idx]
        _chk, _btn, swatch, rgb_lbl, _tol_sld, _tol_spin = self._slot_widgets[idx]
        if slot.color is None:
            swatch.setStyleSheet("background:#555; border:1px solid #777;")
            rgb_lbl.setText(f"{self.PICK_LABELS[idx]}: -")
        else:
            r, g, b = slot.color
            swatch.setStyleSheet(f"background:rgb({r},{g},{b}); border:1px solid #777;")
            rgb_lbl.setText(f"{self.PICK_LABELS[idx]}: ({r}, {g}, {b})")

    def _show_slider_tip(self, slider, title: str, value: int, suffix: str = ""):
        text = f"{title}: {int(value)}{suffix}"
        try:
            slider.setToolTip(text)
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), text, slider)
        except Exception:
            pass

    def _update_feather_label(self):
        self.feather_lbl.setText("Мягкость кеинга")
        self.feather_sld.setToolTip(f"Мягкость кеинга: {self.feather_sld.value()}")

    def _update_vignette_label(self):
        self.vignette_lbl.setText("Мягкость")
        self.vignette_sld.setToolTip(f"Мягкость виньетки: {self.vignette_sld.value()}")

    def _update_window_scale_label(self):
        self.window_scale_lbl.setText("")

    def _on_window_scale_changed(self, value: int):
        if self.owner is None:
            return
        self.owner.state.window_content_scale = int(clamp(value, 70, 100))
        self._update_window_scale_label()
        try:
            self.owner._circle_mask_cache.clear()
            self.owner.update()
        except Exception:
            pass
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_preview_layer_toggled(self, _value: bool):
        if self.owner is None:
            return
        self.owner.state.preview_show_pipettes = bool(self.layer_pipettes_chk.isChecked())
        self.owner.state.preview_show_crop = bool(self.layer_crop_chk.isChecked())
        self.owner.state.preview_show_circle = bool(self.layer_circle_chk.isChecked())
        self.owner.state.preview_show_dimming = bool(self.layer_dim_chk.isChecked())
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_preview_mirror_toggled(self, value: bool):
        if self.owner is None:
            return
        self.owner.state.preview_mirror = bool(value)
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_enabled_toggled(self, value: bool):
        if self.owner is not None and hasattr(self.owner, "set_chroma_enabled"):
            self.owner.set_chroma_enabled(bool(value))
        else:
            self.chroma.enabled = bool(value)

    def _on_slot_enabled(self, idx: int, value: bool):
        self.chroma.picks[idx].enabled = bool(value)

    def _on_slot_tol(self, idx: int, value: int):
        value = int(value)
        self.chroma.picks[idx].tol = value
        _chk, _btn, _sw, _rgb, tol_sld, tol_spin = self._slot_widgets[idx]
        for w in (tol_sld, tol_spin):
            if w.value() != value:
                w.blockSignals(True)
                w.setValue(value)
                w.blockSignals(False)
        self._show_slider_tip(tol_sld, f"Допуск {self.PICK_LABELS[idx]}", value)

    def _begin_pick(self, idx: int):
        self._pick_target = idx
        if not self.chroma.picks[idx].enabled:
            self._slot_widgets[idx][0].setChecked(True)

    def _set_preview_mode(self, mode: str):
        self._preview_mode = mode

    def _on_hsv_changed(self, key: str, end_name: str, value: int):
        attr = f"{key}_{end_name}"
        value = int(value)
        setattr(self.chroma, attr, value)
        self._sync_paired(attr, value)
        self._show_slider_tip(self._hsv_sliders[attr], attr.upper(), value)

    def _sync_paired(self, attr: str, value: int):
        for w in (self._hsv_sliders[attr], self._hsv_spins[attr]):
            if w.value() != value:
                w.blockSignals(True)
                w.setValue(int(value))
                w.blockSignals(False)

    def _on_h_wrap_toggled(self, value: bool):
        self.chroma.h_wrap = bool(value)

    def _fill_hsv_from_pick(self):
        for slot in self.chroma.picks:
            if slot.enabled and slot.color is not None:
                r, g, b = slot.color
                bgr_pixel = np.array([[[b, g, r]]], dtype=np.uint8)
                hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)[0, 0]
                h, s, v = int(hsv_pixel[0]), int(hsv_pixel[1]), int(hsv_pixel[2])
                self.chroma.h_min, self.chroma.h_max = max(0, h - 10), min(179, h + 10)
                self.chroma.s_min, self.chroma.s_max = max(0, s - 50), min(255, s + 50)
                self.chroma.v_min, self.chroma.v_max = max(0, v - 50), min(255, v + 50)
                self.chroma.h_wrap = False
                self._load_from_model()
                self.use_hsv_chk.setChecked(True)
                return
        QMessageBox.information(self, "Нет цвета", "Сначала выберите цвет одной из включённых пипеток.")

    def _on_feather_changed(self, value: int):
        self.chroma.feather = int(value)
        self._update_feather_label()
        self._show_slider_tip(self.feather_sld, "Мягкость кеинга", value)
        if self.chroma.persist and self.owner is not None and hasattr(self.owner, "save_config"):
            self.owner.save_config()

    def _reset_chroma_settings(self):
        if self.owner is not None and hasattr(self.owner, "reset_chroma"):
            ans = QMessageBox.question(
                self,
                "Сбросить?",
                "Сбросить настройки хромакея к значениям по умолчанию?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if ans == QMessageBox.Yes:
                self.owner.reset_chroma()
                self._load_from_model()

    # ------------------------------------------------------------------
    # Виньетка
    # ------------------------------------------------------------------
    def _load_vignette_from_owner(self):
        if self.owner is None:
            return
        st = self.owner.state
        pairs = (
            (self.vignette_on_top_chk, bool(st.always_on_top)),
            (self.vignette_click_through_chk, bool(st.click_through)),
            (self.vignette_mirror_chk, bool(st.window_mirror)),
        )
        for widget, value in pairs:
            widget.blockSignals(True)
            widget.setChecked(value)
            widget.blockSignals(False)
        opacity = int(clamp(getattr(st, "window_opacity", 1.0), 0.2, 1.0) * 100)
        self.vignette_opacity_sld.blockSignals(True)
        self.vignette_opacity_sld.setValue(opacity)
        self.vignette_opacity_sld.blockSignals(False)
        self._update_vignette_opacity_label(opacity)

    def _update_vignette_opacity_label(self, value: int | None = None):
        if value is None:
            value = self.vignette_opacity_sld.value()
        self.vignette_opacity_lbl.setText("Непрозрачность")
        self.vignette_opacity_sld.setToolTip(f"Непрозрачность: {int(value)}%")

    def _on_vignette_on_top(self, value: bool):
        if self.owner is not None:
            self.owner.set_always_on_top(bool(value))

    def _on_vignette_click_through(self, value: bool):
        if self.owner is not None:
            self.owner.set_click_through(bool(value))

    def _on_vignette_mirror(self, value: bool):
        if self.owner is not None:
            self.owner.set_window_mirror(bool(value))

    def _on_vignette_opacity(self, value: int):
        self._update_vignette_opacity_label(value)
        self._show_slider_tip(self.vignette_opacity_sld, "Непрозрачность", value, "%")
        if self.owner is not None:
            self.owner.set_window_opacity_percent(int(value))

    # ------------------------------------------------------------------
    # Кроп
    # ------------------------------------------------------------------
    def _current_crop_mode(self) -> str:
        if self.owner is None:
            return "off"
        return self.owner._current_crop_mode() if hasattr(self.owner, "_current_crop_mode") else (
            "dynamic" if getattr(self.owner.dynamic_crop, "enabled", False)
            else "manual" if getattr(self.owner.crop, "enabled", False)
            else "off"
        )

    def _sync_crop_mode_radios(self):
        mode = self._current_crop_mode()
        pairs = (
            (self.crop_off_rb, mode == "off"),
            (self.crop_manual_rb, mode == "manual"),
            (self.crop_dynamic_rb, mode == "dynamic"),
        )
        for rb, checked in pairs:
            rb.blockSignals(True)
            rb.setChecked(bool(checked))
            rb.blockSignals(False)
        self.crop_enabled_chk.blockSignals(True)
        self.crop_enabled_chk.setChecked(mode == "manual")
        self.crop_enabled_chk.blockSignals(False)
        for _w in getattr(self, "_dynamic_setting_widgets", ()): 
            _w.setEnabled(mode == "dynamic")

    def _on_crop_mode_selected(self, mode: str):
        if self.owner is None:
            return
        if hasattr(self.owner, "set_crop_mode"):
            self.owner.set_crop_mode(mode)
        else:
            self.owner.set_crop_enabled(mode == "manual")
            if hasattr(self.owner, "set_dynamic_crop_enabled"):
                self.owner.set_dynamic_crop_enabled(mode == "dynamic")
        self._sync_crop_mode_radios()
        self._load_dynamic_from_owner()
        self._update_crop_label()

    def _on_crop_enabled(self, value: bool):
        # Совместимость со старым чекбоксом, который больше не показывается.
        if self.owner is None:
            return
        self._on_crop_mode_selected("manual" if value else "off")

    def _reset_crop(self):
        if self.owner is None:
            return
        self.owner.crop.rect = None
        if hasattr(self.owner, "set_crop_mode"):
            self.owner.set_crop_mode("off")
        else:
            self.owner.set_crop_enabled(False)
        self._crop_start_pt = self._crop_end_pt = None
        self._sync_crop_mode_radios()
        self._update_crop_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _capture_full_frame_crop(self):
        if self.owner is None:
            return
        frame = self.get_frame()
        if frame is None:
            return
        h, w = frame.shape[:2]
        self.owner.crop.rect = [0, 0, int(w), int(h)]
        if hasattr(self.owner, "set_crop_mode"):
            self.owner.set_crop_mode("manual")
        else:
            self.owner.set_crop_enabled(True)
        self._sync_crop_mode_radios()
        self._update_crop_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _update_crop_label(self):
        if self.owner is None:
            self.crop_rect_lbl.setText("Кроп: —")
            return
        mode = self._current_crop_mode()
        manual_rect = getattr(self.owner.crop, "rect", None)
        runtime = getattr(self.owner, "_dynamic_crop_runtime", None)
        dyn_rect = getattr(runtime, "crop_rect", None)
        face_found = bool(getattr(runtime, "face_found", False))

        if mode == "dynamic":
            if dyn_rect:
                x, y, w, h = [int(v) for v in dyn_rect]
                status = "лицо найдено" if face_found else "лицо потеряно, держим последнюю область"
                self.crop_rect_lbl.setText(f"Динамический кроп: {x}, {y}, {w}×{h} · {status}")
            else:
                self.crop_rect_lbl.setText("Динамический кроп: ждёт лицо")
            return

        if not manual_rect:
            self.crop_rect_lbl.setText("Кроп: —")
            return
        x, y, w, h = manual_rect
        status = "включён" if mode == "manual" else "сохранён, но выключен"
        self.crop_rect_lbl.setText(f"Кроп: {x}, {y}, {w}×{h} · {status}")

    # ------------------------------------------------------------------
    # Виртуальная камера
    # ------------------------------------------------------------------
    def _update_vcam_scale_label(self):
        self.vcam_scale_lbl.setText(f"Масштаб лица: {self.vcam_scale_sld.value()}%")

    def _update_vcam_vignette_size_label(self):
        self.vcam_vignette_size_lbl.setText(f"Размер виньетки: {self.vcam_vignette_size_sld.value()}%")

    def _update_vcam_bg_label(self):
        if self.owner is None:
            return
        path = self.owner.state.vcam_bg_path or ""
        if not path:
            self.vcam_bg_path_lbl.setText("Подложка: белый фон")
            self.vcam_bg_path_lbl.setStyleSheet("color:#aeb7c2;")
        elif not os.path.exists(path):
            self.vcam_bg_path_lbl.setText(f"Подложка: файл не найден\n{path}")
            self.vcam_bg_path_lbl.setStyleSheet("color:#ff9999;")
        else:
            self.vcam_bg_path_lbl.setText(f"Подложка: {os.path.basename(path)}")
            self.vcam_bg_path_lbl.setStyleSheet("color:#aeb7c2;")

    def _update_vcam_avatar_bg_label(self):
        if self.owner is None:
            return
        color = getattr(self.owner.state, "vcam_avatar_bg_color", "#202128")
        color = self.owner._normalize_hex_color(color, "#202128")
        self.owner.state.vcam_avatar_bg_color = color
        self.vcam_avatar_bg_lbl.setText(f"Фон аватарки: {color}")
        self.vcam_avatar_bg_lbl.setStyleSheet(
            f"color:#aeb7c2; padding-left:18px; "
            f"background:{color}; border:1px solid #2d3b49; border-radius:3px;")

    def _on_vcam_avatar_bg_color(self):
        if self.owner is None:
            return
        current = self.owner._normalize_hex_color(
            getattr(self.owner.state, "vcam_avatar_bg_color", "#202128"),
            "#202128")
        color = QColorDialog.getColor(QtGui.QColor(current), self, "Цвет фона аватарки")
        if not color.isValid():
            return
        self.owner.state.vcam_avatar_bg_color = color.name().upper()
        self._update_vcam_avatar_bg_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _update_vcam_status(self):
        if self.owner is None:
            return
        live = self.owner.vcam is not None
        if live:
            self.vcam_status_lbl.setText(f"● виртуальная LIVE · {self.owner.vcam_w}×{self.owner.vcam_h} · {self.owner.fps or 30} FPS")
            self.vcam_status_lbl.setStyleSheet("color:#38c172;")
        else:
            self.vcam_status_lbl.setText("○ виртуальная камера остановлена")
            self.vcam_status_lbl.setStyleSheet("color:#aeb7c2;")

    def _on_vcam_enabled(self, value: bool):
        if self.owner is None:
            return
        self.owner.set_vcam_enabled(bool(value))
        self.vcam_enabled_chk.blockSignals(True)
        self.vcam_enabled_chk.setChecked(bool(self.owner.state.vcam_enabled))
        self.vcam_enabled_chk.blockSignals(False)
        self._update_vcam_status()
        self._render_vcam_preview()

    def _set_vcam_running(self, value: bool):
        if self.owner is None:
            return
        self.vcam_enabled_chk.setChecked(bool(value))
        self.owner.set_vcam_enabled(bool(value))
        self._update_vcam_status()

    def _restart_vcam(self):
        if self.owner is None:
            return
        try:
            self.owner._stop_vcam()
            self.owner.state.vcam_enabled = True
            self.owner.act_vcam_enable.setChecked(True)
            self.owner._start_vcam()
        finally:
            self.vcam_enabled_chk.blockSignals(True)
            self.vcam_enabled_chk.setChecked(bool(self.owner.state.vcam_enabled))
            self.vcam_enabled_chk.blockSignals(False)
            self._update_vcam_status()

    def _restart_vcam_if_enabled(self):
        if self.owner is None or not bool(getattr(self.owner.state, "vcam_enabled", False)):
            return
        try:
            self.owner._stop_vcam()
            self.owner._start_vcam()
        except Exception as e:
            _log_exc("Перезапуск виртуальной камеры", e)
        self._update_vcam_status()

    def _on_vcam_mirror(self, value: bool):
        if self.owner is not None:
            self.owner.set_vcam_mirror(bool(value))

    def _on_vcam_circle_overlay(self, value: bool):
        if self.owner is None:
            return
        self.owner.state.vcam_circle_overlay = bool(value)
        self.owner._circle_mask_cache.clear()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_vcam_native(self, value: bool):
        if self.owner is None:
            return
        self.owner.state.vcam_passthrough_native = bool(value)
        self._update_vcam_native_dependents()
        if self.owner.state.vcam_enabled and self.owner.vcam is not None:
            try:
                self.owner._stop_vcam()
                self.owner._start_vcam()
            except Exception:
                pass
        if self.owner.chroma.persist:
            self.owner.save_config()
        self._update_vcam_status()

    def _update_vcam_native_dependents(self):
        active = not self.vcam_native_chk.isChecked()
        for w in (self.vcam_mode_combo, self.vcam_circle_overlay_chk,
                  self.vcam_bg_load_btn, self.vcam_bg_telemost_btn, self.vcam_bg_clear_btn,
                  self.vcam_avatar_bg_lbl, self.vcam_avatar_bg_color_btn,
                  self.vcam_cx_spin, self.vcam_cy_spin,
                  self.vcam_cr_sld, self.vcam_cr_spin):
            w.setEnabled(active)

    def _on_vcam_circle_r_changed(self, value: int):
        if self.owner is None:
            return
        value = int(clamp(value, self.vcam_cr_sld.minimum(), self.vcam_cr_sld.maximum()))
        sender = self.sender()
        for w in (self.vcam_cr_sld, self.vcam_cr_spin):
            if w is sender:
                continue
            w.blockSignals(True)
            w.setValue(value)
            w.blockSignals(False)
        self.owner.state.vcam_circle_r = value
        self._show_slider_tip(self.vcam_cr_sld, "R", value)
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_vcam_scale(self, value: int):
        if self.owner is None:
            return
        self.owner.state.vcam_scale = int(clamp(value, 50, 200))
        self._update_vcam_scale_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_vcam_vignette_size(self, value: int):
        if self.owner is None:
            return
        self.owner.state.vcam_vignette_scale = int(clamp(value, 50, 100))
        self._update_vcam_vignette_size_label()
        try:
            self.owner._circle_mask_cache.clear()
        except Exception:
            pass
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_vcam_mode_combo(self, _idx: int):
        if self.owner is None:
            return
        mode = self.vcam_mode_combo.currentData() or "passthrough"
        mode = str(mode)
        if self.owner.state.vcam_mode == mode:
            return
        was_enabled = bool(getattr(self.owner.state, "vcam_enabled", False))
        self.owner.state.vcam_mode = mode
        if was_enabled:
            self._restart_vcam_if_enabled()
        if self.owner.chroma.persist:
            self.owner.save_config()
        self._update_vcam_status()

    def _on_vcam_load_bg(self):
        if self.owner is None:
            return
        start = ""
        prev = self.owner.state.vcam_bg_path
        if prev and os.path.isdir(os.path.dirname(prev)):
            start = os.path.dirname(prev)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фон",
            start,
            "Изображения (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not path:
            return
        self.owner.state.vcam_bg_path = os.path.abspath(path)
        self.owner._bg_cache = {"path": "", "img": None}
        self._update_vcam_bg_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _ensure_telemost_bg_png(self) -> str:
        if not HAVE_QTSVG or QSvgRenderer is None:
            raise RuntimeError("PyQt5.QtSvg недоступен. Нужен для генерации встроенного фона.")
        out_dir = Path(_data_dir()) / "vcam_backgrounds"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "telemost_clean_circle.png"
        svg = VCamSettingsDialog._build_telemost_svg().encode("utf-8")
        renderer = QSvgRenderer(QtCore.QByteArray(svg))
        if not renderer.isValid():
            raise RuntimeError("Не удалось инициализировать SVG для фона Телемоста.")
        image = QImage(855, 511, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        renderer.render(painter)
        painter.end()
        if not image.save(str(out_path), "PNG"):
            raise RuntimeError(f"Не удалось сохранить PNG-фон: {out_path}")
        return str(out_path)

    def _on_vcam_telemost_bg(self):
        if self.owner is None:
            return
        # Режим Телемост теперь собирается слоями:
        # 1) нижняя подложка: белая, если файл не выбран;
        # 2) та же виньетка, что в плавающем окне;
        # 3) верхний фон аватарки с круглым вырезом.
        self.owner.state.vcam_bg_path = ""
        self.owner._bg_cache = {"path": "", "img": None}
        self.owner.state.vcam_circle_x = 422
        self.owner.state.vcam_circle_y = 240
        self.owner.state.vcam_circle_r = 150
        self.owner.state.vcam_mode = "circle"
        self.owner.state.vcam_scale = 100
        self.owner.state.vcam_vignette_scale = 100
        self.owner.state.vcam_circle_overlay = True
        self.owner.state.vcam_passthrough_native = False
        self.owner.state.vcam_mirror = False
        self.owner.state.vcam_avatar_bg_color = "#202128"
        self._load_vcam_from_owner()
        self._restart_vcam_if_enabled()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_vcam_clear_bg(self):
        if self.owner is None:
            return
        self.owner.state.vcam_bg_path = ""
        self.owner._bg_cache = {"path": "", "img": None}
        self._update_vcam_bg_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _redetect_vcam_circle(self, silent=True):
        if self.owner is None:
            return
        bg = self.owner._load_vcam_bg()
        if bg is None:
            if not silent:
                QMessageBox.information(self, "Нет фона", "Сначала загрузите фоновую картинку.")
            return
        result = self.owner.detect_white_circle(bg)
        if result is None:
            if not silent:
                QMessageBox.information(self, "Круг не найден", "Круг не найден автоматически. Установите X/Y/R вручную.")
            h, w = bg.shape[:2]
            cx, cy, cr = w // 2, h // 2, min(w, h) // 4
        else:
            cx, cy, cr = result
        self.owner.state.vcam_circle_x = int(cx)
        self.owner.state.vcam_circle_y = int(cy)
        self.owner.state.vcam_circle_r = int(cr)
        h, w = bg.shape[:2]
        self.vcam_cx_spin.setRange(0, max(1, w))
        self.vcam_cy_spin.setRange(0, max(1, h))
        r_max = max(1, min(w, h) // 2)
        self.vcam_cr_spin.setRange(1, r_max)
        self.vcam_cr_sld.setRange(1, r_max)
        for sp, val in ((self.vcam_cx_spin, cx), (self.vcam_cy_spin, cy),
                        (self.vcam_cr_spin, cr), (self.vcam_cr_sld, cr)):
            sp.blockSignals(True)
            sp.setValue(int(clamp(val, sp.minimum(), sp.maximum())))
            sp.blockSignals(False)
        if self.owner.chroma.persist:
            self.owner.save_config()

    # ------------------------------------------------------------------
    # Preview helpers / crop mouse
    # ------------------------------------------------------------------
    def eventFilter(self, obj, ev):
        if obj is self.preview_label:
            t = ev.type()
            if t == QtCore.QEvent.MouseButtonPress:
                if ev.button() == Qt.RightButton:
                    self._reset_crop()
                    return True
                if ev.button() == Qt.LeftButton:
                    if self._pick_target is not None:
                        self._pick_color_at(ev.pos())
                        return True
                    self._crop_dragging = True
                    self._crop_start_pt = self._crop_end_pt = ev.pos()
                    return True
            if t == QtCore.QEvent.MouseMove and self._crop_dragging:
                self._crop_end_pt = ev.pos()
                return True
            if t == QtCore.QEvent.MouseButtonRelease and ev.button() == Qt.LeftButton and self._crop_dragging:
                self._crop_dragging = False
                self._crop_end_pt = ev.pos()
                self._apply_crop_from_drag()
                return True
        return super().eventFilter(obj, ev)

    def _preview_fit(self, frame):
        h, w = frame.shape[:2]
        ls = self.preview_label.size()
        scale = min(ls.width() / w, ls.height() / h)
        dw, dh = max(1, int(w * scale)), max(1, int(h * scale))
        ox, oy = (ls.width() - dw) // 2, (ls.height() - dh) // 2
        return scale, ox, oy, dw, dh

    def _preview_is_mirrored(self) -> bool:
        if self.owner is not None:
            return bool(getattr(self.owner.state, "preview_mirror", False))
        return bool(getattr(self, "preview_mirror_chk", None) and self.preview_mirror_chk.isChecked())

    def _frame_x_to_preview(self, x: float, frame_w: int, scale: float, ox: int) -> float:
        if self._preview_is_mirrored():
            return ox + (float(frame_w) - float(x)) * scale
        return ox + float(x) * scale

    def _frame_rect_to_preview(self, x: float, y: float, rw: float, rh: float,
                               frame_w: int, scale: float, ox: int, oy: int) -> QtCore.QRectF:
        if self._preview_is_mirrored():
            px = ox + (float(frame_w) - float(x) - float(rw)) * scale
        else:
            px = ox + float(x) * scale
        return QtCore.QRectF(px, oy + float(y) * scale,
                             max(1.0, float(rw) * scale),
                             max(1.0, float(rh) * scale))

    def _preview_x_to_frame(self, preview_x: float, frame_w: int, scale: float, ox: int) -> float:
        x = (float(preview_x) - float(ox)) / max(1e-9, float(scale))
        if self._preview_is_mirrored():
            return float(frame_w) - 1.0 - x
        return x

    def _preview_rect_to_frame_rect(self, rect: QtCore.QRect, frame_w: int, frame_h: int,
                                    scale: float, ox: int, oy: int) -> list[int]:
        dx1 = (float(rect.left()) - float(ox)) / max(1e-9, float(scale))
        dx2 = (float(rect.right() + 1) - float(ox)) / max(1e-9, float(scale))
        dy1 = (float(rect.top()) - float(oy)) / max(1e-9, float(scale))
        dy2 = (float(rect.bottom() + 1) - float(oy)) / max(1e-9, float(scale))
        if self._preview_is_mirrored():
            fx1 = float(frame_w) - dx2
            fx2 = float(frame_w) - dx1
        else:
            fx1, fx2 = dx1, dx2
        x1 = int(clamp(min(fx1, fx2), 0, max(0, frame_w - 1)))
        y1 = int(clamp(min(dy1, dy2), 0, max(0, frame_h - 1)))
        x2 = int(clamp(max(fx1, fx2), x1 + 1, frame_w))
        y2 = int(clamp(max(dy1, dy2), y1 + 1, frame_h))
        return [x1, y1, max(1, x2 - x1), max(1, y2 - y1)]

    def _pick_color_at(self, pos):
        frame = self.get_frame()
        if frame is None or self._pick_target is None:
            return
        h, w = frame.shape[:2]
        scale, ox, oy, _dw, _dh = self._preview_fit(frame)
        x = int(round(self._preview_x_to_frame(pos.x(), w, scale, ox)))
        y = int((pos.y() - oy) / scale)
        if not (0 <= x < w and 0 <= y < h):
            return
        b, g, r = frame[y, x]
        idx = self._pick_target
        self.chroma.picks[idx].color = [int(r), int(g), int(b)]
        self.chroma.picks[idx].pos = [int(x), int(y)]
        self._refresh_slot_visual(idx)
        self._pick_target = None

    def _apply_crop_from_drag(self):
        if self.owner is None:
            return
        frame = self.get_frame()
        if frame is None or self._crop_start_pt is None or self._crop_end_pt is None:
            return
        rect = QtCore.QRect(self._crop_start_pt, self._crop_end_pt).normalized()
        if rect.width() < 8 or rect.height() < 8:
            return
        h, w = frame.shape[:2]
        scale, ox, oy, _dw, _dh = self._preview_fit(frame)
        x, y, rw, rh = self._preview_rect_to_frame_rect(rect, w, h, scale, ox, oy)
        self.owner.crop.rect = [x, y, rw, rh]
        if hasattr(self.owner, "set_crop_mode"):
            self.owner.set_crop_mode("manual")
        else:
            self.owner.set_crop_enabled(True)
        self._sync_crop_mode_radios()
        self._update_crop_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _render_all_previews(self):
        self._render_main_preview()
        self._render_vignette_preview()
        self._render_vcam_preview()
        self._update_camera_status()
        self._update_vcam_status()

    def _preview_qcolor(self, name: str, default: str) -> QtGui.QColor:
        return QtGui.QColor(_style_token(f"preview-{name}", default))

    def _preview_pen(self, name: str, default: str, style=Qt.SolidLine, multiplier: float = 1.0) -> QtGui.QPen:
        base_width = _style_float_token("preview-line-width", 0.23)
        if name in ("manual-crop", "inactive-crop", "dynamic-crop", "composition-circle", "drag-crop"):
            base_width += _style_float_token("preview-crop-circle-extra-width", 0.70)
        width = max(0.1, base_width * float(multiplier))
        pen = QtGui.QPen(self._preview_qcolor(name, default))
        pen.setStyle(style)
        pen.setWidthF(width)
        return pen

    def _render_main_preview(self):
        frame = self.get_frame()
        if frame is None:
            self.preview_label.setText("Нет сигнала")
            return
        h, w = frame.shape[:2]
        ls = self.preview_label.size()
        if ls.width() < 8 or ls.height() < 8:
            return
        scale, ox, oy, dw, dh = self._preview_fit(frame)
        preview_mirror = self._preview_is_mirrored()
        display_frame = cv2.flip(frame, 1) if preview_mirror else frame
        if self._preview_mode == "mask":
            alpha = self._build_alpha_safe(frame)
            if preview_mirror:
                alpha = cv2.flip(alpha, 1)
            disp_bgr = cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR)
            rgb = cv2.cvtColor(disp_bgr, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888).copy()
            pix = QPixmap.fromImage(qimg).scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif self._preview_mode == "result":
            alpha = self._build_alpha_safe(frame)
            if preview_mirror:
                alpha = cv2.flip(alpha, 1)
            rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            argb = np.dstack((rgb, alpha))
            qimg = QImage(argb.data, w, h, w * 4, QImage.Format_RGBA8888).copy()
            scaled = QPixmap.fromImage(qimg).scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pix = QPixmap(dw, dh)
            pix.fill(Qt.transparent)
            p2 = QPainter(pix)
            self._draw_checkerboard(p2, 0, 0, dw, dh, 12)
            p2.drawPixmap(0, 0, scaled)
            p2.end()
        else:
            rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888).copy()
            pix = QPixmap.fromImage(qimg).scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        canvas = QPixmap(ls)
        canvas.fill(QtGui.QColor("#0b121a"))
        p = QPainter(canvas)
        p.drawPixmap(ox, oy, pix)

        show_pipettes = bool(self.layer_pipettes_chk.isChecked())
        show_crop = bool(self.layer_crop_chk.isChecked())
        show_circle = bool(self.layer_circle_chk.isChecked())
        show_dimming = bool(self.layer_dim_chk.isChecked())

        # Пипетки
        if show_pipettes:
            for i, slot in enumerate(self.chroma.picks):
                if not slot.enabled or slot.pos is None or slot.color is None:
                    continue
                fx, fy = slot.pos
                dx, dy = int(round(self._frame_x_to_preview(fx, w, scale, ox))), int(fy * scale) + oy
                r, g, b = slot.color
                p.setPen(self._preview_pen("pipette-border", "#ffffff"))
                p.setBrush(QtGui.QBrush(QtGui.QColor(r, g, b)))
                p.drawEllipse(QtCore.QPoint(dx, dy), 7, 7)
                p.drawText(dx + 10, dy - 8, self.PICK_LABELS[i])

        circle_rect = self._preview_circle_rect(scale, ox, oy, dw, dh, w)
        if circle_rect is not None and (show_circle or show_dimming):
            p.setRenderHint(QPainter.Antialiasing, True)
            if show_dimming:
                outer = QtGui.QPainterPath()
                outer.addRect(QtCore.QRectF(ox, oy, dw, dh))
                hole = QtGui.QPainterPath()
                hole.addEllipse(QtCore.QRectF(circle_rect))
                p.fillPath(outer.subtracted(hole), QtGui.QColor(0, 0, 0, 115))
            if show_circle:
                p.setPen(self._preview_pen("composition-circle", "#d9e2ec", Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(circle_rect)

        # Границы активного кропа и захвата лица.
        if show_crop and self.owner is not None:
            manual_rect = getattr(self.owner.crop, "rect", None)
            mode = self.owner._current_crop_mode() if hasattr(self.owner, "_current_crop_mode") else (
                "dynamic" if getattr(self.owner.dynamic_crop, "enabled", False)
                else "manual" if getattr(self.owner.crop, "enabled", False)
                else "off"
            )
            runtime = getattr(self.owner, "_dynamic_crop_runtime", None)
            dynamic_rect = getattr(runtime, "crop_rect", None)
            face = getattr(runtime, "face", None)
            circle = getattr(runtime, "circle", None)

            if manual_rect:
                x, y, rw, rh = manual_rect
                pen_name = "manual-crop" if mode == "manual" else "inactive-crop"
                pen_default = "#2ea8ff" if mode == "manual" else "#68727e"
                p.setPen(self._preview_pen(pen_name, pen_default, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawRect(self._frame_rect_to_preview(x, y, rw, rh, w, scale, ox, oy))

            if mode == "dynamic" and dynamic_rect:
                x, y, rw, rh = dynamic_rect
                p.setPen(self._preview_pen("dynamic-crop", "#ffcc4d"))
                p.setBrush(Qt.NoBrush)
                p.drawRect(self._frame_rect_to_preview(x, y, rw, rh, w, scale, ox, oy))

            if mode == "dynamic" and circle is not None:
                p.setRenderHint(QPainter.Antialiasing, True)
                r = float(circle.diameter) / 2.0
                rect = self._frame_rect_to_preview(circle.cx - r, circle.cy - r,
                                                   circle.diameter, circle.diameter,
                                                   w, scale, ox, oy)
                p.setPen(self._preview_pen("composition-circle", "#ffd166", Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(rect)
                cfg = self.owner.dynamic_crop
                zone = float(circle.diameter) * clamp(float(getattr(cfg, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE)), 0.0, 0.30)
                if zone > 0:
                    target_face_x = circle.cx + (float(getattr(cfg, "offset_x", 0.0)) - float(getattr(cfg, "circle_offset_x", 0.0))) * circle.diameter
                    target_face_y = circle.cy + (float(getattr(cfg, "offset_y", -0.05)) - float(getattr(cfg, "circle_offset_y", 0.0))) * circle.diameter
                    zr = self._frame_rect_to_preview(target_face_x - zone, target_face_y - zone,
                                                     zone * 2.0, zone * 2.0,
                                                     w, scale, ox, oy)
                    p.setPen(self._preview_pen("inactive-crop", "#68727e", Qt.DotLine, multiplier=0.8))
                    p.drawRect(zr)

            if mode == "dynamic" and face is not None:
                p.setPen(self._preview_pen("face-capture", "#2ea8ff"))
                p.setBrush(Qt.NoBrush)
                p.drawRect(self._frame_rect_to_preview(face.x, face.y, face.w, face.h, w, scale, ox, oy))

        # Drag-кроп
        if show_crop and self._crop_start_pt is not None and self._crop_end_pt is not None:
            rect = QtCore.QRect(self._crop_start_pt, self._crop_end_pt).normalized()
            if rect.width() > 4 and rect.height() > 4:
                p.setPen(self._preview_pen("drag-crop", "#ad7cff"))
                p.setBrush(Qt.NoBrush)
                p.drawRect(rect)

        # Центральная цель
        p.setPen(self._preview_pen("crosshair", "#dce6f0"))
        cx, cy = ls.width() // 2, ls.height() // 2
        p.drawLine(cx - 12, cy, cx + 12, cy)
        p.drawLine(cx, cy - 12, cx, cy + 12)
        p.end()
        self.preview_label.setPixmap(canvas)

    def _preview_circle_rect(self, scale: float, ox: int, oy: int, dw: int, dh: int, frame_w: int | None = None):
        base = QtCore.QRectF(ox, oy, dw, dh)
        active_rect = None
        if self.owner is not None:
            mode = self.owner._current_crop_mode() if hasattr(self.owner, "_current_crop_mode") else "off"
            if mode == "dynamic":
                runtime = getattr(self.owner, "_dynamic_crop_runtime", None)
                active_rect = getattr(runtime, "crop_rect", None)
            elif mode == "manual":
                active_rect = getattr(self.owner.crop, "rect", None)
        if active_rect:
            x, y, rw, rh = active_rect
            if frame_w is not None:
                base = self._frame_rect_to_preview(x, y, rw, rh, frame_w, scale, ox, oy)
            else:
                base = QtCore.QRectF(int(x * scale) + ox, int(y * scale) + oy,
                                     max(1, int(rw * scale)), max(1, int(rh * scale)))
        d = max(1.0, min(base.width(), base.height()))
        return QtCore.QRectF(base.center().x() - d / 2.0,
                             base.center().y() - d / 2.0,
                             d, d)

    def _render_vignette_preview(self):
        frame = self.get_frame()
        if frame is None or self.owner is None:
            self.vignette_preview_lbl.setText("Нет кадра")
            return
        rgb = self._compose_window_preview_rgb(frame)
        if rgb is None:
            self.vignette_preview_lbl.setText("—")
            return
        self._put_rgb_to_label(rgb, self.vignette_preview_lbl)

    def _render_vcam_preview(self):
        if self.owner is not None and not bool(getattr(self.owner.state, "vcam_enabled", False)):
            self.vcam_preview_lbl.clear()
            self.vcam_preview_lbl.setText("Виртуальная камера выключена")
            self.vcam_preview_lbl.setEnabled(False)
            return
        self.vcam_preview_lbl.setEnabled(True)
        frame = self.get_frame()
        if frame is None or self.owner is None:
            self.vcam_preview_lbl.setText("Нет кадра")
            return
        src = frame
        owner = self.owner
        saved_w, saved_h = owner.vcam_w, owner.vcam_h
        if saved_w <= 0 or saved_h <= 0:
            owner.vcam_h, owner.vcam_w = src.shape[:2]
        try:
            rgb = owner._compose_vcam_frame(src)
        except Exception as e:
            _log_exc("integrated vcam preview", e)
            rgb = None
        finally:
            owner.vcam_w, owner.vcam_h = saved_w, saved_h
        if rgb is None:
            self.vcam_preview_lbl.setText("—")
            return
        self._put_rgb_to_label(rgb, self.vcam_preview_lbl)

    def _apply_owner_crop(self, frame):
        if self.owner is None:
            return frame

        # Важно: предпросмотр виньетки должен использовать тот же активный
        # кроп, что и плавающее окно. Детектор здесь повторно не запускаем —
        # берём последний runtime из основного QTimer/_on_tick.
        if getattr(self.owner.dynamic_crop, "enabled", False):
            runtime = getattr(self.owner, "_dynamic_crop_runtime", None)
            rect = getattr(runtime, "crop_rect", None)
            if rect and hasattr(self.owner, "_crop_rect_with_padding"):
                crop = self.owner._crop_rect_with_padding(frame, rect)
                if crop is not None:
                    return crop
            return frame

        if not self.owner.crop.enabled or not self.owner.crop.rect:
            return frame
        x, y, w, h = self.owner.crop.rect
        fh, fw = frame.shape[:2]
        x = int(clamp(x, 0, fw - 1))
        y = int(clamp(y, 0, fh - 1))
        w = int(clamp(w, 1, fw - x))
        h = int(clamp(h, 1, fh - y))
        return frame[y:y + h, x:x + w].copy()

    def _compose_window_preview_rgb(self, frame):
        owner = self.owner
        src = self._apply_owner_crop(frame)
        disp = cv2.flip(src, 1) if owner.state.window_mirror else src
        target = 360
        h, w = disp.shape[:2]
        scale = max(target / max(1, w), target / max(1, h))
        nw, nh = max(1, int(ceil(w * scale))), max(1, int(ceil(h * scale)))
        rs = cv2.resize(disp, (nw, nh), interpolation=cv2.INTER_LINEAR)
        sx = max(0, (rs.shape[1] - target) // 2)
        sy = max(0, (rs.shape[0] - target) // 2)
        roi = rs[sy:sy + target, sx:sx + target].copy()
        if roi.shape[0] != target or roi.shape[1] != target:
            pad = np.zeros((target, target, 3), dtype=roi.dtype)
            pad[:roi.shape[0], :roi.shape[1]] = roi
            roi = pad

        circle_size = min(roi.shape[:2])
        if owner.state.window_shape == "circle":
            content_scale = clamp(getattr(owner.state, "window_content_scale", 100) / 100.0, 0.70, 1.00)
            circle_size = max(1, int(round(circle_size * content_scale)))
            if circle_size < min(roi.shape[:2]):
                roi = owner._shrink_into_canvas(roi, target, target, scale=content_scale)

        alpha = owner._build_alpha(roi) if owner.chroma.enabled else np.full((roi.shape[0], roi.shape[1]), 255, dtype=np.uint8)
        if owner.state.window_shape == "circle":
            cm = owner._circle_mask(circle_size)
            sm = np.zeros((roi.shape[0], roi.shape[1]), dtype=np.uint8)
            oy = (roi.shape[0] - circle_size) // 2
            ox = (roi.shape[1] - circle_size) // 2
            sm[oy:oy + circle_size, ox:ox + circle_size] = cm
            alpha = (alpha.astype(np.uint16) * sm // 255).astype(np.uint8)

        bg = np.full_like(roi, 15)
        a3 = (alpha.astype(np.float32) / 255.0)[..., None]
        out = (roi.astype(np.float32) * a3 + bg.astype(np.float32) * (1 - a3)).astype(np.uint8)
        return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)

    def _put_rgb_to_label(self, rgb, label: QLabel):
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg).scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pix)

    def _build_alpha_safe(self, bgr) -> np.ndarray:
        try:
            if self.owner is not None and hasattr(self.owner, "_build_alpha"):
                return self.owner._build_alpha(bgr)
        except Exception:
            pass
        return np.full(bgr.shape[:2], 255, dtype=np.uint8)

    @staticmethod
    def _draw_checkerboard(painter: QPainter, x: int, y: int, w: int, h: int, cell: int = 12):
        c1 = QtGui.QColor(60, 60, 60)
        c2 = QtGui.QColor(90, 90, 90)
        for j in range(0, h, cell):
            for i in range(0, w, cell):
                color = c1 if ((i // cell + j // cell) % 2 == 0) else c2
                painter.fillRect(x + i, y + j, min(cell, w - i), min(cell, h - j), color)

# ---------------------------------------------------------------------------
# Диалог редактирования горячих клавиш
# ---------------------------------------------------------------------------
class HotkeysDialog(QDialog):
    """Окно редактирования горячих клавиш.

    Для каждого действия из HOTKEY_DEFINITIONS показывается
    QKeySequenceEdit. При сохранении проверяется, что не появилось
    дубликатов (две разные строки с одинаковой клавишей) — конфликты
    подсвечиваются красным, и кнопка «Сохранить» неактивна.

    «Сброс к дефолтам» возвращает все шорткаты к DEFAULT_HOTKEYS.
    Применяется без рестарта программы — owner._apply_hotkeys()
    моментально перевешивает QShortcut'ы и QAction.setShortcut.
    """
    def __init__(self, parent, current: dict, owner=None):
        super().__init__(parent)
        self.setWindowTitle("Горячие клавиши")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.setStyleSheet(STYLE_QSS)
        self.owner = owner
        # Словарь: hid → QKeySequenceEdit
        self._editors: dict = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(8)

        intro = QLabel(
            "Кликните в поле и нажмите желаемую комбинацию клавиш. "
            "Чтобы очистить — нажмите Backspace. "
            "Конфликты будут подсвечены красным."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#bbb; padding:0 0 4px 0;")
        root.addWidget(intro)

        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        for row, (hid, title, _default, _kind, _aattr) in enumerate(HOTKEY_DEFINITIONS):
            lbl = QLabel(title)
            ed  = QtWidgets.QKeySequenceEdit()
            seq = current.get(hid, "")
            if seq:
                ed.setKeySequence(QtGui.QKeySequence(seq))
            ed.setFixedWidth(180)
            ed.keySequenceChanged.connect(self._validate)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(ed,  row, 1)
            self._editors[hid] = ed
        root.addLayout(grid)

        # Подсказка о статусе валидации
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color:#f88;")
        root.addWidget(self.status_lbl)

        # Кнопки
        btn_row = QHBoxLayout()
        self.reset_btn  = QPushButton("Сброс к дефолтам")
        self.cancel_btn = QPushButton("Отмена")
        self.save_btn   = QPushButton("Сохранить")
        self.save_btn.setDefault(True)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

        self.reset_btn.clicked.connect(self._reset_to_defaults)
        self.cancel_btn.clicked.connect(self.close)
        self.save_btn.clicked.connect(self._save)

        # Первичная валидация (на случай если в config уже были конфликты)
        self._validate()

    def _validate(self):
        """Подсвечивает дубликаты и блокирует «Сохранить» при конфликте."""
        seen: dict = {}   # seq_str → список hid
        for hid, ed in self._editors.items():
            seq_str = ed.keySequence().toString()
            if seq_str:
                seen.setdefault(seq_str, []).append(hid)

        bad_hids = set()
        for seq_str, hids in seen.items():
            if len(hids) > 1:
                bad_hids.update(hids)

        # Перекрашиваем поля
        for hid, ed in self._editors.items():
            if hid in bad_hids:
                ed.setStyleSheet(
                    "QKeySequenceEdit { border:1px solid #f55; background:#3a1e1e; }")
            else:
                ed.setStyleSheet("")

        if bad_hids:
            self.status_lbl.setText(
                f"Конфликт: одна и та же комбинация назначена нескольким "
                f"действиям ({len(bad_hids)} шт.). Исправьте.")
            self.save_btn.setEnabled(False)
        else:
            self.status_lbl.setText("")
            self.save_btn.setEnabled(True)

    def _reset_to_defaults(self):
        for hid, ed in self._editors.items():
            seq = DEFAULT_HOTKEYS.get(hid, "")
            ed.setKeySequence(QtGui.QKeySequence(seq) if seq
                              else QtGui.QKeySequence())
        self._validate()

    def _save(self):
        """Записывает новые значения в owner.hotkeys, переприменяет
        привязки и сохраняет config.json (если persist)."""
        new_map = {}
        for hid, ed in self._editors.items():
            new_map[hid] = ed.keySequence().toString()
        if self.owner is not None:
            self.owner.hotkeys = new_map
            if hasattr(self.owner, "_apply_hotkeys"):
                self.owner._apply_hotkeys()
            if getattr(self.owner.chroma, "persist", False):
                self.owner.save_config()
        _logger.info("Горячие клавиши обновлены")
        self.accept()

# ---------------------------------------------------------------------------
# Диалог настроек виртуальной камеры
# ---------------------------------------------------------------------------
class VCamSettingsDialog(QDialog):
    """Диалог настроек виртуальной камеры (v17).

    Содержит:
      • Чекбокс «Включена», «Отразить зеркально».
      • Ползунок «Масштаб лица» 50–200%.
      • Радиокнопки выбора режима композиции:
          – Без фона (passthrough);
          – Простая подкладка фона;
          – Лицо в круг (имитация аватарки видеосервиса).
      • Кнопка «Загрузить фон…» — открывает QFileDialog,
        запоминает абсолютный путь, при выборе автоматически
        пытается обнаружить белый круг (HoughCircles).
      • Кнопка «Для Телемоста» — создаёт и подставляет встроенный
        фон-подложку с кругом, сразу выставляя координаты круга.
      • Поля X / Y / Радиус для ручной правки положения круга.
      • Превью результата (живое, обновляется по таймеру).
    """

    def __init__(self, parent, owner):
        super().__init__(parent)
        self.setWindowTitle("Виртуальная камера")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.setStyleSheet(STYLE_QSS)
        self.owner = owner

        # ----- Виджеты -----
        self.enabled_chk = QCheckBox("Включена")
        f = self.enabled_chk.font(); f.setBold(True)
        self.enabled_chk.setFont(f)
        self.mirror_chk  = QCheckBox("Отразить зеркально")
        # v13.3: «голый» режим — отдавать в vcam кадр 1:1 как с
        # физической камеры, в её нативном разрешении, без обработки.
        # При включении vcam пере-стартует.
        self.native_chk  = QCheckBox(
            "Отдавать как с физической камеры (без обработки)")
        # Круглая виньетка поверх кадра vcam — имитирует круглое окно
        # в самой виртуальной камере. Нужно когда хочется чтобы Телемост
        # и другие сервисы видели именно круг (а не квадратный кадр
        # с прозрачными зонами от кеинга).
        self.circle_overlay_chk = QCheckBox(
            "Обводить круглой виньеткой (как в окне)")

        self.scale_sld   = QSlider(Qt.Horizontal); self.scale_sld.setRange(50, 200)
        self.scale_lbl   = QLabel("Масштаб лица: 100%")
        self.vignette_size_sld = QSlider(Qt.Horizontal); self.vignette_size_sld.setRange(50, 100)
        self.vignette_size_lbl = QLabel("Размер виньетки: 100%")

        self.mode_off_rb     = QtWidgets.QRadioButton("Без фона")
        self.mode_bg_rb      = QtWidgets.QRadioButton("Простая подкладка фона")
        self.mode_circle_rb  = QtWidgets.QRadioButton("Лицо в круг (как в Телемост)")
        mode_grp = QtWidgets.QButtonGroup(self)
        for rb in (self.mode_off_rb, self.mode_bg_rb, self.mode_circle_rb):
            mode_grp.addButton(rb)

        self.bg_path_lbl = QLabel("Фон: не выбран")
        self.bg_path_lbl.setStyleSheet("color:#bbb;")
        self.bg_path_lbl.setWordWrap(True)
        self.bg_load_btn = QPushButton("Загрузить фон…")
        self.bg_telemost_btn = QPushButton("Для Телемоста")
        self.bg_clear_btn= QPushButton("Сброс")

        self.auto_chk    = QCheckBox("Авто-детект круга при загрузке")
        self.cx_spin     = QSpinBox(); self.cx_spin.setRange(0, 9999)
        self.cy_spin     = QSpinBox(); self.cy_spin.setRange(0, 9999)
        self.cr_spin     = QSpinBox(); self.cr_spin.setRange(1, 9999)
        self.redetect_btn= QPushButton("Найти круг повторно")

        self.preview_lbl = QLabel(self)
        self.preview_lbl.setMinimumSize(360, 200)
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setStyleSheet("background:#0a0a0a; border:1px solid #444;")

        self.status_lbl  = QLabel("")
        self.status_lbl.setStyleSheet("color:#bbb;")
        self.status_lbl.setWordWrap(True)

        self.close_btn   = QPushButton("Закрыть")
        self.close_btn.setDefault(True)

        # ----- Компоновка -----
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(8)

        # Шапка: чекбоксы вкл/зеркало
        top = QHBoxLayout()
        top.addWidget(self.enabled_chk); top.addSpacing(20)
        top.addWidget(self.mirror_chk);  top.addStretch(1)
        root.addLayout(top)

        # v13.3: «голый» режим — самый верх, потому что он отключает
        # все остальные настройки ниже.
        root.addWidget(self.native_chk)
        # Круглая виньетка
        root.addWidget(self.circle_overlay_chk)

        # Превью
        prev_box = QGroupBox("Превью")
        pv = QVBoxLayout(prev_box)
        pv.addWidget(self.preview_lbl)
        root.addWidget(prev_box)

        # Кадр
        frame_box = QGroupBox("Кадр виртуальной камеры")
        fl = QGridLayout(frame_box)
        fl.addWidget(self.scale_lbl, 0, 0)
        fl.addWidget(self.scale_sld, 0, 1, 1, 3)
        fl.addWidget(self.vignette_size_lbl, 1, 0)
        fl.addWidget(self.vignette_size_sld, 1, 1, 1, 3)
        root.addWidget(frame_box)

        # Режим
        mode_box = QGroupBox("Режим")
        ml = QVBoxLayout(mode_box)
        ml.addWidget(self.mode_off_rb)
        ml.addWidget(self.mode_bg_rb)
        ml.addWidget(self.mode_circle_rb)
        root.addWidget(mode_box)

        # Фон
        bg_box = QGroupBox("Фон")
        bl = QGridLayout(bg_box)
        row = 0
        bl.addWidget(self.bg_load_btn,      row, 0)
        bl.addWidget(self.bg_telemost_btn, row, 1)
        bl.addWidget(self.bg_clear_btn,     row, 2)
        bl.addWidget(self.bg_path_lbl,      row, 3, 1, 3)
        row += 1
        bl.addWidget(self.auto_chk,     row, 0, 1, 6); row += 1
        bl.addWidget(QLabel("Круг X"),  row, 0); bl.addWidget(self.cx_spin, row, 1)
        bl.addWidget(QLabel("Y"),       row, 2); bl.addWidget(self.cy_spin, row, 3)
        bl.addWidget(QLabel("R"),       row, 4); bl.addWidget(self.cr_spin, row, 5)
        row += 1
        bl.addWidget(self.redetect_btn, row, 0, 1, 6)
        root.addWidget(bg_box)

        root.addWidget(self.status_lbl)

        # Кнопка
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.close_btn)
        root.addLayout(btn_row)

        # ----- Сигналы -----
        self.enabled_chk.toggled.connect(self._on_enabled)
        self.mirror_chk.toggled.connect(self._on_mirror)
        self.native_chk.toggled.connect(self._on_native)
        self.circle_overlay_chk.toggled.connect(self._on_circle_overlay)
        self.scale_sld.valueChanged.connect(self._on_scale)
        self.vignette_size_sld.valueChanged.connect(self._on_vignette_size)
        self.mode_off_rb.toggled.connect(
            lambda v: v and self._set_mode("passthrough"))
        self.mode_bg_rb.toggled.connect(
            lambda v: v and self._set_mode("background"))
        self.mode_circle_rb.toggled.connect(
            lambda v: v and self._set_mode("circle"))
        self.bg_load_btn.clicked.connect(self._on_load_bg)
        self.bg_telemost_btn.clicked.connect(self._on_telemost_bg)
        self.bg_clear_btn.clicked.connect(self._on_clear_bg)
        self.auto_chk.toggled.connect(
            lambda v: setattr(self.owner.state, "vcam_circle_auto", bool(v)))
        self.cx_spin.valueChanged.connect(
            lambda v: setattr(self.owner.state, "vcam_circle_x", int(v)))
        self.cy_spin.valueChanged.connect(
            lambda v: setattr(self.owner.state, "vcam_circle_y", int(v)))
        self.cr_spin.valueChanged.connect(
            lambda v: setattr(self.owner.state, "vcam_circle_r", int(v)))
        self.redetect_btn.clicked.connect(self._redetect_circle)
        self.close_btn.clicked.connect(self.close)

        self._load_from_owner()

        # Превью обновляется ~10 fps — важна не плавность, а отзывчивость
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._render_preview)
        self._timer.start(100)

    # ==================================================================
    # Загрузка из модели
    # ==================================================================
    def _load_from_owner(self):
        st = self.owner.state
        for w, val in ((self.enabled_chk,        st.vcam_enabled),
                        (self.mirror_chk,         st.vcam_mirror),
                        (self.native_chk,         st.vcam_passthrough_native),
                        (self.circle_overlay_chk, st.vcam_circle_overlay)):
            w.blockSignals(True); w.setChecked(bool(val)); w.blockSignals(False)
        self._update_native_dependents()
        self.scale_sld.blockSignals(True)
        self.scale_sld.setValue(int(clamp(st.vcam_scale, 50, 200)))
        self.scale_sld.blockSignals(False)
        self.vignette_size_sld.blockSignals(True)
        self.vignette_size_sld.setValue(int(clamp(
            getattr(st, "vcam_vignette_scale", 100), 50, 100)))
        self.vignette_size_sld.blockSignals(False)
        self._update_scale_label()
        self._update_vignette_size_label()
        # Режим
        rb = {"passthrough": self.mode_off_rb,
              "background":  self.mode_bg_rb,
              "circle":      self.mode_circle_rb}.get(
                  st.vcam_mode, self.mode_off_rb)
        rb.blockSignals(True); rb.setChecked(True); rb.blockSignals(False)
        # Фон
        self._update_bg_label()
        for w in (self.auto_chk, self.cx_spin, self.cy_spin, self.cr_spin):
            w.blockSignals(True)
        self.auto_chk.setChecked(bool(st.vcam_circle_auto))
        self.cx_spin.setValue(int(st.vcam_circle_x))
        self.cy_spin.setValue(int(st.vcam_circle_y))
        self.cr_spin.setValue(int(st.vcam_circle_r) if st.vcam_circle_r > 0 else 1)
        for w in (self.auto_chk, self.cx_spin, self.cy_spin, self.cr_spin):
            w.blockSignals(False)
        # Статус
        if not HAVE_PYVIRTUALCAM:
            self.status_lbl.setText(
                "Модуль pyvirtualcam не установлен — отправка в виртуальную "
                "камеру недоступна. Установите: pip install pyvirtualcam")
            self.enabled_chk.setEnabled(False)
        else:
            self.status_lbl.setText("")

    def _update_scale_label(self):
        self.scale_lbl.setText(f"Масштаб лица: {self.scale_sld.value()}%")

    def _update_vignette_size_label(self):
        self.vignette_size_lbl.setText(
            f"Размер виньетки: {self.vignette_size_sld.value()}%")

    def _update_bg_label(self):
        path = self.owner.state.vcam_bg_path or ""
        if not path:
            self.bg_path_lbl.setText("Фон: не выбран")
        elif not os.path.exists(path):
            self.bg_path_lbl.setText(f"Фон: ⚠ файл не найден\n{path}")
            self.bg_path_lbl.setStyleSheet("color:#f88;")
        else:
            base = os.path.basename(path)
            self.bg_path_lbl.setText(f"Фон: {base}")
            self.bg_path_lbl.setStyleSheet("color:#bbb;")

    # ==================================================================
    # Обработчики
    # ==================================================================
    def _on_enabled(self, v: bool):
        if hasattr(self.owner, "set_vcam_enabled"):
            self.owner.set_vcam_enabled(bool(v))
        if self.enabled_chk.isChecked() != self.owner.state.vcam_enabled:
            self.enabled_chk.blockSignals(True)
            self.enabled_chk.setChecked(self.owner.state.vcam_enabled)
            self.enabled_chk.blockSignals(False)

    def _on_mirror(self, v: bool):
        if hasattr(self.owner, "set_vcam_mirror"):
            self.owner.set_vcam_mirror(bool(v))

    def _on_circle_overlay(self, v: bool):
        self.owner.state.vcam_circle_overlay = bool(v)
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_native(self, v: bool):
        """v13.3: переключение «как с физической камеры».
        Если vcam сейчас работает — пере-стартуем её, чтобы
        pyvirtualcam подхватил новый размер кадра."""
        v = bool(v)
        self.owner.state.vcam_passthrough_native = v
        self._update_native_dependents()
        # Пере-старт vcam если она запущена — pyvirtualcam.Camera
        # не умеет менять width/height на лету.
        if self.owner.state.vcam_enabled and self.owner.vcam is not None:
            try:
                self.owner._stop_vcam()
                self.owner._start_vcam()
            except Exception:
                pass
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _update_native_dependents(self):
        """В режиме native все остальные настройки vcam теряют смысл
        (они обрабатывают кадр, а в native обработки нет). Делаем их
        неактивными, чтобы пользователь видел причинно-следственную
        связь."""
        active = not self.native_chk.isChecked()
        for w in (self.scale_sld, self.scale_lbl,
                  self.vignette_size_sld, self.vignette_size_lbl,
                  self.mode_off_rb, self.mode_bg_rb, self.mode_circle_rb,
                  self.bg_load_btn, self.bg_telemost_btn, self.bg_clear_btn,
                  self.auto_chk, self.cx_spin, self.cy_spin, self.cr_spin,
                  self.redetect_btn, self.circle_overlay_chk):
            w.setEnabled(active)

    def _on_scale(self, v: int):
        self.owner.state.vcam_scale = int(v)
        self._update_scale_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_vignette_size(self, v: int):
        self.owner.state.vcam_vignette_scale = int(clamp(v, 50, 100))
        self._update_vignette_size_label()
        try:
            self.owner._circle_mask_cache.clear()
        except Exception:
            pass
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _set_mode(self, mode: str):
        self.owner.state.vcam_mode = mode
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_load_bg(self):
        # Стартовая директория — папка предыдущего фона, если был
        start = ""
        prev = self.owner.state.vcam_bg_path
        if prev and os.path.isdir(os.path.dirname(prev)):
            start = os.path.dirname(prev)
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фон",
            start,
            "Изображения (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path:
            return
        # Сохраняем абсолютный путь
        self.owner.state.vcam_bg_path = os.path.abspath(path)
        # Сбрасываем кэш фона у владельца, чтобы _load_vcam_bg перечитал
        self.owner._bg_cache = {"path": "", "img": None}
        self._update_bg_label()
        # Авто-детект круга, если включён
        if self.owner.state.vcam_circle_auto:
            self._redetect_circle(silent=False)
        if self.owner.chroma.persist:
            self.owner.save_config()

    @staticmethod
    def _build_telemost_svg() -> str:
        """Встроенный SVG-фон для режима «как в Телемост»."""
        W, H = 855, 511
        CX, CY = 422, 240
        R = 150
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     xmlns="http://www.w3.org/2000/svg">

  <defs>
    <radialGradient id="bgGrad" cx="50%" cy="45%" r="75%">
      <stop offset="0%" stop-color="#26262b"/>
      <stop offset="70%" stop-color="#222329"/>
      <stop offset="100%" stop-color="#202128"/>
    </radialGradient>

    <radialGradient id="circleGrad" cx="50%" cy="42%" r="62%">
      <stop offset="0%" stop-color="#f0f0f0"/>
      <stop offset="45%" stop-color="#e8e8e8"/>
      <stop offset="78%" stop-color="#dddddd"/>
      <stop offset="100%" stop-color="#d4d4d4"/>
    </radialGradient>

    <filter id="softBlur" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="18"/>
    </filter>

    <filter id="grain" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise"
                    baseFrequency="0.018"
                    numOctaves="3"
                    seed="8"
                    result="noise"/>
      <feColorMatrix type="matrix"
        values="
          0.18 0    0    0 0.82
          0    0.18 0    0 0.82
          0    0    0.18 0 0.82
          0    0    0    0.18 0"/>
      <feBlend mode="multiply" in2="SourceGraphic"/>
    </filter>

    <clipPath id="circleClip">
      <circle cx="{CX}" cy="{CY}" r="{R}"/>
    </clipPath>
  </defs>

  <rect x="0" y="0" width="{W}" height="{H}" fill="url(#bgGrad)"/>

  <circle cx="{CX}" cy="{CY}" r="{R}"
          fill="url(#circleGrad)"
          filter="url(#grain)"/>

  <g clip-path="url(#circleClip)" filter="url(#softBlur)">
    <ellipse cx="{CX - 58}" cy="{CY + 25}" rx="50" ry="85"
             fill="#cfcfcf" opacity="0.18"/>

    <ellipse cx="{CX + 70}" cy="{CY - 10}" rx="65" ry="90"
             fill="#ffffff" opacity="0.20"/>

    <ellipse cx="{CX - 12}" cy="{CY - 62}" rx="115" ry="60"
             fill="#ffffff" opacity="0.16"/>

    <ellipse cx="{CX + 28}" cy="{CY + 72}" rx="110" ry="42"
             fill="#c9c9c9" opacity="0.13"/>
  </g>

  <circle cx="{CX}" cy="{CY}" r="{R}"
          fill="none"
          stroke="#d8d8d8"
          stroke-width="1"
          opacity="0.35"/>

</svg>
"""

    def _ensure_telemost_bg_png(self) -> str:
        """Создаёт PNG-фон для Телемоста в папке данных и возвращает путь."""
        if not HAVE_QTSVG or QSvgRenderer is None:
            raise RuntimeError(
                "Модуль PyQt5.QtSvg недоступен. Нужен для генерации встроенного фона.")

        out_dir = Path(_data_dir()) / "vcam_backgrounds"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "telemost_clean_circle.png"

        svg = self._build_telemost_svg().encode("utf-8")
        renderer = QSvgRenderer(QtCore.QByteArray(svg))
        if not renderer.isValid():
            raise RuntimeError("Не удалось инициализировать SVG для фона Телемоста.")

        image = QImage(855, 511, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        renderer.render(painter)
        painter.end()

        if not image.save(str(out_path), "PNG"):
            raise RuntimeError(f"Не удалось сохранить PNG-фон: {out_path}")

        return str(out_path)

    def _on_telemost_bg(self):
        """Подставляет встроенный фон «Для Телемоста»."""
        try:
            path = self._ensure_telemost_bg_png()
        except Exception as e:
            QMessageBox.warning(self, "Фон Телемоста", str(e))
            return

        self.owner.state.vcam_bg_path = os.path.abspath(path)
        self.owner._bg_cache = {"path": "", "img": None}

        self.owner.state.vcam_circle_x = 422
        self.owner.state.vcam_circle_y = 240
        self.owner.state.vcam_circle_r = 150
        self.owner.state.vcam_mode = "circle"
        self.owner.state.vcam_scale = 78
        self.owner.state.vcam_vignette_scale = 50
        self.owner.state.vcam_circle_overlay = True
        self.owner.state.vcam_passthrough_native = False
        self.owner.state.vcam_mirror = False

        self._update_bg_label()
        self.cx_spin.setRange(0, 855)
        self.cy_spin.setRange(0, 511)
        self.cr_spin.setRange(1, min(855, 511) // 2)
        for sp, val in ((self.cx_spin, 422), (self.cy_spin, 240), (self.cr_spin, 150)):
            sp.blockSignals(True)
            sp.setValue(val)
            sp.blockSignals(False)

        self.mode_circle_rb.blockSignals(True)
        self.mode_circle_rb.setChecked(True)
        self.mode_circle_rb.blockSignals(False)

        for w, val in ((self.mirror_chk, False),
                       (self.native_chk, False),
                       (self.circle_overlay_chk, True)):
            w.blockSignals(True)
            w.setChecked(val)
            w.blockSignals(False)
        for sld, val in ((self.scale_sld, 78),
                         (self.vignette_size_sld, 50)):
            sld.blockSignals(True)
            sld.setValue(val)
            sld.blockSignals(False)
        self._update_scale_label()
        self._update_vignette_size_label()
        self._update_native_dependents()

        if self.owner.chroma.persist:
            self.owner.save_config()

    def _on_clear_bg(self):
        self.owner.state.vcam_bg_path = ""
        self.owner._bg_cache = {"path": "", "img": None}
        self._update_bg_label()
        if self.owner.chroma.persist:
            self.owner.save_config()

    def _redetect_circle(self, silent=True):
        bg = self.owner._load_vcam_bg()
        if bg is None:
            if not silent:
                QMessageBox.information(self, "Нет фона",
                                         "Сначала загрузите фоновую картинку.")
            return
        result = self.owner.detect_white_circle(bg)
        if result is None:
            if not silent:
                QMessageBox.information(
                    self, "Круг не найден",
                    "Не удалось автоматически найти белый круг на фоне.\n"
                    "Установите параметры (X, Y, Радиус) вручную.")
            # Поставим круг в центр фона как стартовую позицию
            h, w = bg.shape[:2]
            cx, cy, cr = w // 2, h // 2, min(w, h) // 4
        else:
            cx, cy, cr = result
            _logger.info("vcam: круг детектирован: (%d,%d) r=%d", cx, cy, cr)
        self.owner.state.vcam_circle_x = cx
        self.owner.state.vcam_circle_y = cy
        self.owner.state.vcam_circle_r = cr
        # Подгоняем диапазон спинбоксов под фон
        h, w = bg.shape[:2]
        self.cx_spin.setRange(0, max(1, w))
        self.cy_spin.setRange(0, max(1, h))
        self.cr_spin.setRange(1, max(1, min(w, h) // 2))
        for sp, val in ((self.cx_spin, cx), (self.cy_spin, cy), (self.cr_spin, cr)):
            sp.blockSignals(True); sp.setValue(int(val)); sp.blockSignals(False)
        if self.owner.chroma.persist:
            self.owner.save_config()

    # ==================================================================
    # Превью
    # ==================================================================
    def _render_preview(self):
        # Если диалог стал невидим (свернули в трей и закрыли) — не считаем
        if not self.isVisible():
            return
        get_frame = getattr(self.owner, "get_last_frame", None)
        frame = get_frame() if get_frame else None
        if frame is None:
            self.preview_lbl.setText("Нет кадра")
            return
        # Используем тот же _compose_vcam_frame, что и реальная vcam.
        # На этапе настройки vcam ещё может быть не запущена — нужно
        # принудительно обеспечить размер. Подставим временно размер
        # под исходник, если vcam_w/h ещё не задан.
        owner = self.owner
        saved_w, saved_h = owner.vcam_w, owner.vcam_h
        if saved_w <= 0 or saved_h <= 0:
            owner.vcam_h, owner.vcam_w = frame.shape[:2]
        try:
            rgb = owner._compose_vcam_frame(frame)
        except Exception as e:
            _log_exc("vcam preview", e)
            rgb = None
        finally:
            owner.vcam_w, owner.vcam_h = saved_w, saved_h
        if rgb is None:
            self.preview_lbl.setText("—")
            return
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888).copy()
        ls = self.preview_lbl.size()
        pix = QPixmap.fromImage(qimg).scaled(
            ls, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_lbl.setPixmap(pix)

# ---------------------------------------------------------------------------
class CropDialog(QDialog):
    def __init__(self, parent, get_frame_callable, initial_rect=None, owner=None):
        super().__init__(parent)
        self.setWindowTitle("Кроп")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(STYLE_QSS)
        self.get_frame    = get_frame_callable
        self.initial_rect = initial_rect
        self.owner        = owner
        self.frame_cache  = None
        self.dragging = False
        self.start_pt = None
        self.end_pt   = None

        # Чекбокс «Включён» — переехал из контекстного меню. Управляет
        # owner.set_crop_enabled, как и пункт меню в старых версиях.
        self.enabled_chk = QCheckBox("Кроп включён")
        font = self.enabled_chk.font(); font.setBold(True)
        self.enabled_chk.setFont(font)
        if owner is not None:
            self.enabled_chk.setChecked(bool(owner.crop.enabled))
            self.enabled_chk.toggled.connect(self._on_enabled)

        self.preview = QLabel(self)
        self.preview.setMinimumSize(640, 360)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background:#111; border:1px solid #444;")

        btn_apply  = QPushButton("Применить")
        btn_reset  = QPushButton("Сброс выделения")
        btn_cancel = QPushButton("Отмена")
        btn_apply.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_reset.clicked.connect(self._reset)

        row = QHBoxLayout()
        row.addWidget(btn_apply); row.addWidget(btn_reset); row.addWidget(btn_cancel)

        lay = QVBoxLayout(self)
        lay.addWidget(self.enabled_chk)
        lay.addWidget(self.preview)
        lay.addWidget(QLabel("ЛКМ — тянуть прямоугольник; ПКМ — сброс; Enter — применить"))
        lay.addLayout(row)

        self.preview.installEventFilter(self)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._render)
        self._timer.start(1000 // 30)

    def _on_enabled(self, v: bool):
        if self.owner is not None and hasattr(self.owner, "set_crop_enabled"):
            self.owner.set_crop_enabled(bool(v))

    def _reset(self):
        self.start_pt = self.end_pt = self.initial_rect = None

    def eventFilter(self, obj, ev):
        if obj is self.preview:
            t = ev.type()
            if t == QtCore.QEvent.MouseButtonPress:
                if ev.button() == Qt.LeftButton:
                    self.dragging = True
                    self.start_pt = self.end_pt = ev.pos()
                elif ev.button() == Qt.RightButton:
                    self._reset()
                return True
            if t == QtCore.QEvent.MouseMove and self.dragging:
                self.end_pt = ev.pos(); return True
            if t == QtCore.QEvent.MouseButtonRelease and ev.button() == Qt.LeftButton:
                self.dragging = False; return True
        return super().eventFilter(obj, ev)

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter): self.accept(); return
        if ev.key() == Qt.Key_Escape:                 self.reject(); return
        super().keyPressEvent(ev)

    def _render(self):
        frame = self.get_frame()
        if frame is None:
            self.preview.setText("Нет сигнала"); return
        self.frame_cache = frame
        h, w = frame.shape[:2]
        lw, lh = self.preview.width(), self.preview.height()
        scale = min(lw / w, lh / h)
        dw, dh = int(w * scale), int(h * scale)
        ox, oy = (lw - dw) // 2, (lh - dh) // 2

        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg  = QImage(rgb.data, w, h, QImage.Format_RGB888)
        pix   = QPixmap.fromImage(qimg).scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        canvas = QPixmap(lw, lh); canvas.fill(Qt.black)
        p = QPainter(canvas)
        p.drawPixmap(ox, oy, pix)

        if self.start_pt and self.end_pt:
            rect = QtCore.QRect(self.start_pt, self.end_pt).normalized()
            p.setPen(QtGui.QPen(Qt.green, 2))
            p.drawRect(rect)
        elif self.initial_rect:
            x, y, rw, rh = self.initial_rect
            p.setPen(QtGui.QPen(Qt.yellow, 2))
            p.drawRect(int(x*scale)+ox, int(y*scale)+oy, int(rw*scale), int(rh*scale))
        p.end()
        self.preview.setPixmap(canvas)

    def selected_rect_source_coords(self):
        if self.frame_cache is None:
            return None
        h, w = self.frame_cache.shape[:2]
        lw, lh = self.preview.width(), self.preview.height()
        scale = min(lw / w, lh / h)
        ox = (lw - int(w * scale)) // 2
        oy = (lh - int(h * scale)) // 2
        if self.start_pt and self.end_pt:
            r  = QtCore.QRect(self.start_pt, self.end_pt).normalized()
            x  = int(clamp((r.x()  - ox) / scale, 0, w - 1))
            y  = int(clamp((r.y()  - oy) / scale, 0, h - 1))
            rw = int(clamp(r.width()  / scale, 1, w - x))
            rh = int(clamp(r.height() / scale, 1, h - y))
            return [x, y, rw, rh]
        return self.initial_rect

# ---------------------------------------------------------------------------
# Основное окно
# ---------------------------------------------------------------------------
class RoundCamWindow(QWidget):

    def __init__(self, args):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self._base_flags = Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.Tool
        self.setWindowFlags(self._base_flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._icon = _load_embedded_icon()
        if self._icon.isNull():
            self._icon = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.setWindowIcon(self._icon)

        self.state  = AppState()
        self.chroma = ChromaConfig()
        self.crop   = CropConfig()
        self.dynamic_crop = DynamicCropConfig()
        self._dynamic_crop_runtime = DynamicCropRuntimeState()
        self._dynamic_face_detector = None
        self._face_director = FaceAutoDirector() if HAVE_FACE_DIRECTOR else None
        self._face_director_last_result = None
        self.ptz = PTZConfig()
        self._ptz_runtime = PTZRuntimeState()

        self.fps        = args.fps
        self.req_width  = args.width
        self.req_height = args.height
        # Override разрешения виртуальной камеры через CLI: если argv-аргумент
        # был задан явно — используем его. Иначе vcam подстроится под физическую
        # камеру (см. _start_vcam: после открытия cap читаем фактическое
        # разрешение и кладём в self.vcam_w/h).
        self.vcam_res_override = getattr(args, "vcam_res_explicit", None)
        if self.vcam_res_override:
            self.vcam_w, self.vcam_h = self.vcam_res_override
        else:
            self.vcam_w = self.vcam_h = 0   # будет заполнено при открытии камеры
        self.vcam       = None
        self.cap        = None
        self._cap_lock = threading.RLock()
        self._capture_loop = CameraCaptureLoop(self._cap_lock)
        self._capture_loop.frame_ready.connect(self._on_capture_frame, Qt.QueuedConnection)
        self._capture_loop.no_frame.connect(self._on_capture_no_frame, Qt.QueuedConnection)
        self._pending_frame_bgr = None
        self._pending_frame_id = 0
        self._processed_frame_id = 0
        self.camera_index     = 0 if args.camera is None else int(args.camera)
        self.last_frame_bgr   = None
        self._no_frame_count  = 0
        self._circle_mask_cache: dict = {}
        # Кэш фоновой картинки и параметров круга
        self._bg_cache: dict = {"path": "", "img": None}
        self._shutdown_started = False
        self._shutdown_done = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_config_now)

        self.load_config()
        if args.camera is None:
            self.camera_index = int(getattr(self.state, "camera_index", self.camera_index))
        else:
            self.state.camera_index = int(self.camera_index)
        self.setWindowOpacity(self.state.window_opacity)

        # Открываем нужную камеру ПЕРВОЙ — до find_cameras,
        # чтобы избежать двойного мигания подсветки.
        # find_cameras потом просто пропустит уже открытый индекс.
        if not self._open_camera(self.camera_index):
            # Попробуем первую из доступных
            backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
            fallback = next((i for i in range(10) if _can_open_camera(i, backend)), None)
            if fallback is None:
                QMessageBox.critical(None, "Ошибка", "Камеры не найдены")
                sys.exit(1)
            _logger.warning("Камера %s недоступна, используем %s",
                            self.camera_index, fallback)
            self.camera_index = fallback
            self.state.camera_index = int(self.camera_index)
            if not self._open_camera(self.camera_index):
                QMessageBox.critical(None, "Ошибка",
                                     f"Не удалось открыть камеру {self.camera_index}")
                sys.exit(1)
            self.save_config()

        # Теперь находим все камеры, пропуская уже открытую
        self.available_cameras = find_cameras(skip_index=self.camera_index)
        if not self.available_cameras:
            self.available_cameras = [self.camera_index]
        self.camera_names = {}
        self._refresh_camera_names()

        # Перед resize/move проверим: сохранённая позиция всё ещё на экране?
        # Если внешний монитор отключили — окно «улетит» туда, где его не достать.
        size = self.state.circle_diameter
        if not self._is_position_visible(self.state.pos_x, self.state.pos_y, size):
            x, y, size = self._safe_window_geometry()
            self.state.pos_x, self.state.pos_y = x, y
            self.state.circle_diameter = size
            _logger.warning(
                "Сохранённая позиция вне доступных экранов — сброс на главный")

        self.resize(self.state.circle_diameter, self.state.circle_diameter)
        self.move(self.state.pos_x, self.state.pos_y)
        self._update_mask()

        self._frame_timer = QTimer(self)
        self._frame_timer.timeout.connect(self._on_tick)
        self._frame_timer.start(int(1000 / (self.fps or 30)))

        # Горячие клавиши.
        # Все шорткаты создаются через _apply_hotkeys() из словаря
        # self.hotkeys. Это позволяет диалогу «Hotkeys…» переназначать
        # клавиши без перезапуска.
        # Если load_config() уже создал self.hotkeys (нашёл секцию
        # в config.json) — не перетираем; иначе ставим дефолты.
        self._shortcuts = []
        if not hasattr(self, "hotkeys"):
            self.hotkeys = dict(DEFAULT_HOTKEYS)

        # Открытый диалог хромакея — храним ссылку для повторного открытия
        # (вместо создания нового окна каждый раз) и для синхронизации
        # ползунка виньетки при изменении из контекстного меню
        self._chroma_dlg = None
        self._hotkeys_dlg = None
        self._vcam_dlg = None

        self._build_menus()
        # Шорткаты создаём ПОСЛЕ build_menus — у act_chroma и act_chroma_cfg
        # были setShortcut, мы их сейчас тоже обновим через _apply_hotkeys.
        self._apply_hotkeys()

    # ------------------------------------------------------------------
    # Открытие камеры — единственная точка
    # ------------------------------------------------------------------
    def _open_camera(self, index: int) -> bool:
        if getattr(self, "_shutdown_started", False):
            return False
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        self._stop_capture_loop(release=True, log=False)
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            try:
                cap.release()
            except Exception:
                pass
            return False
        try:
            if self.req_width and self.req_height:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.req_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.req_height)
            if self.fps:
                cap.set(cv2.CAP_PROP_FPS, self.fps)
        except Exception as e:
            _log_exc("Ошибка настройки камеры", e)
        self.cap = cap
        self._pending_frame_bgr = None
        self._pending_frame_id = 0
        self._processed_frame_id = 0
        _log_cap(cap)
        self._capture_loop.set_capture(cap, int(index), int(self.fps or 30))
        _logger.info("Камера %s открыта, захват запущен в worker-thread", index)
        return True

    def _on_capture_frame(self, frame):
        if getattr(self, "_shutdown_started", False):
            return
        self._pending_frame_bgr = frame
        self._pending_frame_id += 1

    def _on_capture_no_frame(self, missed: int):
        self._no_frame_count = int(missed)
        if missed in (1, 30, 100):
            _logger.warning("Нет кадра (worker count=%d)", missed)

    def _stop_capture_loop(self, release: bool = True, log: bool = True):
        try:
            if getattr(self, "_capture_loop", None) is not None:
                self._capture_loop.stop_capture(release=release, wait=True)
        except Exception as e:
            _log_exc("Ошибка остановки worker-захвата", e)
        if release:
            self.cap = None
        self._pending_frame_bgr = None
        if log:
            _logger.info("Физическая камера освобождена")

    # ------------------------------------------------------------------
    # Построение меню
    # ------------------------------------------------------------------
    def _sub(self, parent: QMenu, title: str) -> QMenu:
        """Создаёт подменю. Стиль наследуется от родителя автоматически
        (благодаря глобальному QApplication.setStyleSheet(STYLE_QSS))."""
        m = QMenu(title, self)
        parent.addMenu(m)
        return m

    def _slider_row(self, parent_menu: QMenu, prefix: str,
                    lo: int, hi: int, val: int):
        """Создаёт QWidgetAction с лейблом и ползунком для меню.
        Возвращает (action, label, slider)."""
        lbl = QLabel(f"{prefix}: {val}")
        lbl.setStyleSheet("color:rgba(255,255,255,0.92); min-width:128px;")
        sld = QSlider(Qt.Horizontal)
        sld.setRange(lo, hi); sld.setValue(val)
        w   = QWidget(parent_menu)
        lay = QHBoxLayout(w); lay.setContentsMargins(10, 6, 10, 6)
        lay.addWidget(lbl); lay.addWidget(sld)
        wa  = QWidgetAction(parent_menu); wa.setDefaultWidget(w)
        return wa, lbl, sld

    def _build_menus(self):
        # ---- Общие QAction (используются в обоих меню) ----
        self.act_on_top      = QAction("Всегда поверх",        self, checkable=True)
        self.act_mirror      = QAction("Отразить зеркально",   self, checkable=True)
        self.act_click_thru  = QAction("Прокликиваемый",       self, checkable=True)
        self.act_vcam_enable = QAction("Вкл/выкл",             self, checkable=True)
        self.act_vcam_mirror = QAction("Отразить зеркально",   self, checkable=True)
        self.act_vcam_fill   = QAction("По ширине окна",        self, checkable=True)
        self.act_chroma      = QAction("Хромакей: вкл/выкл",   self, checkable=True)
        self.act_chroma_cfg  = QAction("Свойства…",             self)
        self.act_chroma_settings = QAction("Настройки хромакея / виньетки…", self)
        self.act_crop_off    = QAction("Выключен",             self, checkable=True)
        self.act_crop_manual = QAction("Включен",              self, checkable=True)
        self.act_dynamic_crop = QAction("Динамический",         self, checkable=True)
        self.act_dynamic_crop.setToolTip("Автокомпозиция лица для плавающего окна. Ручной кроп не изменяет.")
        self.act_dynamic_debug = QAction("Показывать разметку динамического кропа", self, checkable=True)
        self.act_dynamic_reset = QAction("Сбросить параметры динамического кропа", self)
        self.act_ptz_home_save = QAction("Запомнить базовое положение камеры и цели", self)
        self.act_ptz_home_reset = QAction("Вернуть камеру и цель к базе", self)
        self.act_target_left = QAction("← Цель", self)
        self.act_target_right = QAction("Цель →", self)
        self.act_target_up = QAction("↑ Цель", self)
        self.act_target_down = QAction("Цель ↓", self)
        self.act_crop_enable = QAction("Кроп: вкл/выкл",       self, checkable=True)
        self.act_crop_pick   = QAction("Настройки кропа…",     self)

        self._crop_mode_group = QActionGroup(self)
        self._crop_mode_group.setExclusive(True)
        self._crop_mode_group.addAction(self.act_crop_off)
        self._crop_mode_group.addAction(self.act_crop_manual)
        self._crop_mode_group.addAction(self.act_dynamic_crop)
        self.act_vcam_settings = QAction("Виртуальная камера…", self)
        self.act_shape_circ  = QAction("Круг",   self, checkable=True)
        self.act_shape_sq    = QAction("Квадрат",self, checkable=True)
        self.act_cam_toggle  = QAction("Выключить камеру",     self)
        self.act_cam_refresh = QAction("Обновить список камер", self)
        self.act_size_up     = QAction("Увеличить окно",        self)
        self.act_size_down   = QAction("Уменьшить окно",        self)
        self.act_ptz_settings = QAction("Настройки PTZ…",       self)
        self.act_about       = QAction("О программе…",         self)
        self.act_hotkeys     = QAction("Hotkeys…",             self)
        self.act_exit        = QAction("Выход",                 self)
        # Сброс
        self.act_reset_pos   = QAction("Позиция и размер окна", self)
        self.act_reset_chroma = QAction("Сбросить хромакей",    self)
        self.act_reset_all   = QAction("Сбросить всё…",         self)

        grp_shape = QActionGroup(self)
        grp_shape.setExclusive(True)
        grp_shape.addAction(self.act_shape_circ)
        grp_shape.addAction(self.act_shape_sq)

        # Действия камер — создаются один раз, добавляются в оба меню.
        # Группа эксклюзивная, чтобы пункты выглядели как радиокнопки.
        self._cam_group   = QActionGroup(self)
        self._cam_group.setExclusive(True)
        self._cam_actions = []
        for idx in self.available_cameras:
            a = QAction(self.camera_display_name(idx, include_props=False), self, checkable=True)
            a.setData(int(idx))
            a.setChecked(idx == self.camera_index)
            a.triggered.connect(lambda _, i=idx: self.switch_camera(i))
            self._cam_group.addAction(a)
            self._cam_actions.append(a)

        # ---- Контекстное меню окна ----
        self.ctx_menu = QMenu(self)
        self.ctx_menu.aboutToShow.connect(
            lambda: self.ctx_menu.setWindowOpacity(self.chroma.ui_opacity))
        self._fill_menu(self.ctx_menu, is_tray=False)

        # ---- Меню трея ----
        self.tray_act_show = QAction("Показать окно", self, checkable=True, checked=True)
        self.tray_act_show.toggled.connect(self._on_tray_show)

        self.tray_menu = QMenu(self)
        self.tray_menu.aboutToShow.connect(
            lambda: self.tray_menu.setWindowOpacity(self.chroma.ui_opacity))
        self.tray_menu.addAction(self.tray_act_show)
        self._fill_menu(self.tray_menu, is_tray=True)

        # ---- Трей ----
        self.tray = QSystemTrayIcon(self._icon, self)
        self.tray.setToolTip(APP_NAME)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(
            lambda r: self.tray_menu.popup(QtGui.QCursor.pos())
            if r in (QSystemTrayIcon.Trigger, QSystemTrayIcon.Context) else None)
        self.tray.show()

        # ---- Подключение сигналов ----
        self.act_on_top.toggled.connect(self.set_always_on_top)
        self.act_mirror.toggled.connect(self.set_window_mirror)
        self.act_click_thru.toggled.connect(self.set_click_through)
        self.act_vcam_enable.toggled.connect(self.set_vcam_enabled)
        self.act_vcam_mirror.toggled.connect(self.set_vcam_mirror)
        self.act_vcam_fill.toggled.connect(
            lambda v: setattr(self.state, "vcam_fit", "fill" if v else "letterbox"))
        self.act_chroma.toggled.connect(self.set_chroma_enabled)
        # Пункт «Хромакей…» в меню теперь сразу открывает диалог,
        # а не подменю «Вкл/выкл / Настройки». act_chroma_cfg всё
        # равно нужен — у него хоткей Ctrl+K.
        self.act_chroma_cfg.triggered.connect(self._open_chroma_dialog)
        self.act_chroma_settings.triggered.connect(self._open_chroma_settings)
        self.act_size_up.triggered.connect(lambda checked=False: self._scale_circle(1))
        self.act_size_down.triggered.connect(lambda checked=False: self._scale_circle(-1))
        self.act_ptz_settings.triggered.connect(self._open_ptz_settings)
        self.act_crop_off.triggered.connect(lambda checked=False: checked and self.set_crop_mode("off"))
        self.act_crop_manual.triggered.connect(lambda checked=False: checked and self.set_crop_mode("manual"))
        self.act_dynamic_crop.triggered.connect(lambda checked=False: checked and self.set_crop_mode("dynamic"))
        self.act_dynamic_debug.toggled.connect(self.set_dynamic_debug_view)
        self.act_dynamic_reset.triggered.connect(self._dynamic_reset)
        self.act_ptz_home_save.triggered.connect(self._ptz_remember_home)
        self.act_ptz_home_reset.triggered.connect(self._reset_camera_and_target_to_home)
        self.act_target_left.triggered.connect(lambda: self._dynamic_arrow_nudge("x", -1))
        self.act_target_right.triggered.connect(lambda: self._dynamic_arrow_nudge("x", 1))
        self.act_target_up.triggered.connect(lambda: self._dynamic_arrow_nudge("y", -1))
        self.act_target_down.triggered.connect(lambda: self._dynamic_arrow_nudge("y", 1))
        self.act_crop_enable.toggled.connect(self.set_crop_enabled)
        self.act_crop_pick.triggered.connect(self._open_crop_settings)
        self.act_shape_circ.toggled.connect(
            lambda v: v and self._set_window_shape("circle"))
        self.act_shape_sq.toggled.connect(
            lambda v: v and self._set_window_shape("square"))
        self.act_cam_toggle.triggered.connect(self.toggle_camera)
        self.act_cam_refresh.triggered.connect(self.refresh_cameras)
        self.act_about.triggered.connect(self._show_about)
        self.act_hotkeys.triggered.connect(self._open_hotkeys_dialog)
        self.act_vcam_settings.triggered.connect(self._open_vcam_settings)
        self.act_exit.triggered.connect(self.force_quit)
        self.act_reset_pos.triggered.connect(self.reset_window_geometry)
        self.act_reset_chroma.triggered.connect(self.reset_chroma)
        self.act_reset_all.triggered.connect(self.reset_all)

        # Начальное состояние кнопок из модели
        self.set_always_on_top(self.state.always_on_top)
        self.set_window_mirror(self.state.window_mirror)
        self.set_click_through(self.state.click_through)
        self.set_vcam_enabled(self.state.vcam_enabled)
        self.set_vcam_mirror(self.state.vcam_mirror)
        self.set_chroma_enabled(self.chroma.enabled)
        self.set_crop_mode(self._current_crop_mode(), save=False)
        self._set_window_shape(self.state.window_shape)
        self.act_vcam_fill.setChecked(self.state.vcam_fit == "fill")
        self._update_cam_label()

    def _spin_action(self, parent_menu: QMenu, label: str, widget: QWidget) -> QWidgetAction:
        row = QWidget(parent_menu)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(8)
        lbl = QLabel(label)
        lbl.setMinimumWidth(150)
        lay.addWidget(lbl)
        lay.addWidget(widget)
        act = QWidgetAction(parent_menu)
        act.setDefaultWidget(row)
        return act

    def _make_menu_spin(self, value, minimum, maximum, *, suffix="", step=1, decimals=None, callback=None):
        if decimals is None:
            sp = QSpinBox()
            sp.setRange(int(minimum), int(maximum))
            sp.setSingleStep(int(step))
            sp.setValue(int(value))
        else:
            sp = QtWidgets.QDoubleSpinBox()
            sp.setRange(float(minimum), float(maximum))
            sp.setSingleStep(float(step))
            sp.setDecimals(int(decimals))
            sp.setValue(float(value))
        sp.setKeyboardTracking(False)
        sp.setMinimumWidth(86)
        if suffix:
            sp.setSuffix(suffix)
        if callback is not None:
            sp.valueChanged.connect(callback)
        return sp

    def _make_menu_slider(self, value, minimum, maximum, *, scale=1.0,
                          suffix="", callback=None, width=170):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(round(minimum * scale)), int(round(maximum * scale)))
        slider.setValue(int(round(value * scale)))
        slider.setMinimumWidth(width)
        value_lbl = QLabel("")
        value_lbl.setMinimumWidth(48)
        value_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_lbl.setStyleSheet("color:#aeb7c2;")

        def _fmt(raw: int) -> str:
            val = raw / float(scale)
            if scale >= 100:
                text = f"{val:.2f}"
            elif scale >= 10:
                text = f"{val:.1f}"
            else:
                text = f"{int(round(val))}"
            return text + suffix

        def _changed(raw: int):
            value_lbl.setText(_fmt(raw))
            if callback is not None:
                callback(raw / float(scale))

        slider.valueChanged.connect(_changed)
        value_lbl.setText(_fmt(slider.value()))

        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(slider)
        lay.addWidget(value_lbl)
        return row

    def _set_dynamic_param(self, name: str, value, *, reset_runtime: bool = True):
        cfg = self.dynamic_crop
        if name in ("analysis_scale_percent", "min_face_size_full_frame", "vignette_panel_width"):
            value = int(value)
        elif name in ("arrows_move_face", "invert_arrows_x", "invert_arrows_y", "show_debug_view"):
            value = bool(value)
        else:
            value = float(value)
        setattr(cfg, name, value)
        if name == "position_smoothing":
            cfg.smoothing = float(value)
        elif name == "position_dead_zone":
            cfg.center_dead_zone = float(value)
        max_offset = float(getattr(cfg, "max_composition_offset", MAX_COMPOSITION_OFFSET))
        cfg.offset_x = float(clamp(getattr(cfg, "offset_x", 0.0), -max_offset, max_offset))
        cfg.offset_y = float(clamp(getattr(cfg, "offset_y", -0.05), -max_offset, max_offset))
        cfg.circle_offset_x = float(clamp(getattr(cfg, "circle_offset_x", 0.0), -max_offset, max_offset))
        cfg.circle_offset_y = float(clamp(getattr(cfg, "circle_offset_y", 0.0), -max_offset, max_offset))
        if reset_runtime and name in ("min_face_size_full_frame", "analysis_scale_percent"):
            self._dynamic_crop_runtime = DynamicCropRuntimeState()
            self._reset_face_director()
        self._sync_dynamic_menu_actions()

        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                if hasattr(dlg, "_load_dynamic_from_owner"):
                    dlg._load_dynamic_from_owner()
                if hasattr(dlg, "_update_crop_label"):
                    dlg._update_crop_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        if self.chroma.persist:
            self.save_config()

    def _add_dynamic_crop_menu_controls(self, dyn_m: QMenu):
        cfg = self.dynamic_crop
        dyn_m.addAction(self.act_dynamic_debug)
        dyn_m.addSeparator()
        dyn_m.addAction(self._spin_action(
            dyn_m, "Диаметр круга",
            self._make_menu_slider(cfg.circle_to_head, DYNAMIC_CROP_MIN_CIRCLE_TO_HEAD, DYNAMIC_CROP_MAX_CIRCLE_TO_HEAD, scale=100, callback=lambda v: self._set_dynamic_param("circle_to_head", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Круг X",
            self._make_menu_slider(getattr(cfg, "circle_offset_x", 0.0), -MAX_COMPOSITION_OFFSET, MAX_COMPOSITION_OFFSET, scale=100, callback=lambda v: self._set_dynamic_param("circle_offset_x", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Круг Y",
            self._make_menu_slider(getattr(cfg, "circle_offset_y", 0.0), -MAX_COMPOSITION_OFFSET, MAX_COMPOSITION_OFFSET, scale=100, callback=lambda v: self._set_dynamic_param("circle_offset_y", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Лицо X",
            self._make_menu_slider(getattr(cfg, "offset_x", 0.0), -MAX_COMPOSITION_OFFSET, MAX_COMPOSITION_OFFSET, scale=100, callback=lambda v: self._set_dynamic_param("offset_x", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Лицо Y",
            self._make_menu_slider(getattr(cfg, "offset_y", -0.05), -MAX_COMPOSITION_OFFSET, MAX_COMPOSITION_OFFSET, scale=100, callback=lambda v: self._set_dynamic_param("offset_y", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Запас",
            self._make_menu_slider(getattr(cfg, "crop_padding", DEFAULT_DYNAMIC_CROP_PADDING), 1.0, 1.6, scale=100, callback=lambda v: self._set_dynamic_param("crop_padding", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Плавн. позиция",
            self._make_menu_slider(getattr(cfg, "position_smoothing", getattr(cfg, "smoothing", DEFAULT_SMOOTHING)), 0.0, 0.80, scale=100, callback=lambda v: self._set_dynamic_param("position_smoothing", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Плавн. масштаб",
            self._make_menu_slider(getattr(cfg, "scale_smoothing", 0.22), 0.0, 0.80, scale=100, callback=lambda v: self._set_dynamic_param("scale_smoothing", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Возврат",
            self._make_menu_slider(getattr(cfg, "return_speed", DEFAULT_DYNAMIC_RETURN_SPEED), 0.0, 1.0, scale=100, callback=lambda v: self._set_dynamic_param("return_speed", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Порог позиции",
            self._make_menu_slider(getattr(cfg, "position_dead_zone", getattr(cfg, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE)), 0.0, 0.30, scale=100, callback=lambda v: self._set_dynamic_param("position_dead_zone", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Порог масштаба",
            self._make_menu_slider(getattr(cfg, "scale_dead_zone", 0.08), 0.0, 0.30, scale=100, callback=lambda v: self._set_dynamic_param("scale_dead_zone", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Макс. смещение",
            self._make_menu_slider(getattr(cfg, "max_composition_offset", MAX_COMPOSITION_OFFSET), 0.05, 1.00, scale=100, callback=lambda v: self._set_dynamic_param("max_composition_offset", v, reset_runtime=False))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Анализ кадра",
            self._make_menu_slider(cfg.analysis_scale_percent, DYNAMIC_CROP_ANALYSIS_MIN, DYNAMIC_CROP_ANALYSIS_MAX, scale=1, suffix="%", callback=lambda v: self._set_dynamic_param("analysis_scale_percent", v))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Мин. лицо",
            self._make_menu_slider(getattr(cfg, "min_face_size_full_frame", MIN_FACE_SIZE_FULL_FRAME), 24, 600, scale=1, suffix=" px", callback=lambda v: self._set_dynamic_param("min_face_size_full_frame", v))
        ))
        dyn_m.addAction(self._spin_action(
            dyn_m, "Шаг стрелок",
            self._make_menu_slider(getattr(cfg, "nudge_step", COMPOSITION_NUDGE_STEP), 0.001, 0.100, scale=1000, callback=lambda v: self._set_dynamic_param("nudge_step", v, reset_runtime=False))
        ))
        dyn_m.addSeparator()
        act_move_face = QAction("Стрелки двигают лицо в круге", self, checkable=True)
        act_move_face.setChecked(bool(getattr(cfg, "arrows_move_face", True)))
        act_move_face.toggled.connect(lambda v: self._set_dynamic_param("arrows_move_face", v, reset_runtime=False))
        dyn_m.addAction(act_move_face)
        act_inv_x = QAction("Инвертировать ← / →", self, checkable=True)
        act_inv_x.setChecked(bool(getattr(cfg, "invert_arrows_x", False)))
        act_inv_x.toggled.connect(lambda v: self._set_dynamic_param("invert_arrows_x", v, reset_runtime=False))
        dyn_m.addAction(act_inv_x)
        act_inv_y = QAction("Инвертировать ↑ / ↓", self, checkable=True)
        act_inv_y.setChecked(bool(getattr(cfg, "invert_arrows_y", False)))
        act_inv_y.toggled.connect(lambda v: self._set_dynamic_param("invert_arrows_y", v, reset_runtime=False))
        dyn_m.addAction(act_inv_y)
        dyn_m.addSeparator()
        dyn_m.addAction(self.act_dynamic_reset)

    def _fill_menu(self, menu: QMenu, is_tray: bool):
        """Заполняет контекстное меню окна и меню трея.

        v15: меню снова ближе к старой рабочей логике, но без тяжёлых
        второстепенных элементов. Быстрые действия живут в меню, длинные
        настройки — в общем окне «Свойства…» с вкладками.
        """
        # Камера — верхний быстрый пункт, как в старой версии.
        menu.addAction(self.act_cam_toggle)

        # === Окно ===
        win_m = self._sub(menu, "Окно")
        win_m.addAction(self.act_on_top)
        win_m.addAction(self.act_mirror)
        win_m.addAction(self.act_click_thru)
        win_m.addSeparator()
        win_m.addAction(self.act_shape_circ)
        win_m.addAction(self.act_shape_sq)
        win_m.addSeparator()
        win_m.addAction(self.act_size_up)
        win_m.addAction(self.act_size_down)

        # Камеры оставлены в «Окно», чтобы не ломать старую привычку меню.
        # refresh_cameras использует сохранённые ссылки на меню и anchor.
        cam_separator = win_m.addSeparator()
        if is_tray:
            self._tray_win_menu = win_m
            self._tray_cam_anchor = cam_separator
        else:
            self._ctx_win_menu = win_m
            self._ctx_cam_anchor = cam_separator
        for a in self._cam_actions:
            win_m.addAction(a)
        win_m.addAction(self.act_cam_refresh)

        menu.addSeparator()

        # === Хромакей / виньетка ===
        chroma_m = self._sub(menu, "Хромакей / виньетка")
        chroma_m.addAction(self.act_chroma)
        chroma_m.addAction(self.act_chroma_settings)

        # === Кроп ===
        crop_m = self._sub(menu, "Кроп")
        crop_m.addAction(self.act_crop_off)
        crop_m.addAction(self.act_crop_manual)
        crop_m.addAction(self.act_dynamic_crop)
        crop_m.addSeparator()
        crop_m.addAction(self.act_crop_pick)
        crop_m.addAction(self.act_dynamic_debug)

        # === Виртуальная камера ===
        vcam_m = self._sub(menu, "Виртуальная камера")
        vcam_m.addAction(self.act_vcam_enable)
        vcam_m.addAction(self.act_vcam_mirror)
        vcam_m.addAction(self.act_vcam_settings)

        # === PTZ / цель ===
        ptz_m = self._sub(menu, "PTZ / цель")
        ptz_m.addAction(self.act_ptz_home_save)
        ptz_m.addAction(self.act_ptz_home_reset)
        ptz_m.addSeparator()
        ptz_m.addAction(self.act_ptz_settings)

        # === Настройки и сброс ===
        menu.addSeparator()
        menu.addAction(self.act_chroma_cfg)

        reset_m = self._sub(menu, "Сброс")
        reset_m.addAction(self.act_reset_pos)
        reset_m.addSeparator()
        reset_m.addAction(self.act_reset_chroma)
        reset_m.addAction(self.act_reset_all)

        # === Низ ===
        menu.addSeparator()
        menu.addAction(self.act_hotkeys)
        menu.addAction(self.act_about)
        menu.addSeparator()
        menu.addAction(self.act_exit)

    # ------------------------------------------------------------------
    # Обработчики ползунков — единые для обоих меню
    # ------------------------------------------------------------------
    def set_window_opacity_percent(self, v: int):
        v = int(clamp(v, 20, 100))
        val = clamp(v / 100.0, 0.2, 1.0)
        self.state.window_opacity = val
        self.setWindowOpacity(val)
        self.chroma.ui_opacity = clamp(val, 0.5, 1.0)
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg.vignette_opacity_sld.blockSignals(True)
                dlg.vignette_opacity_sld.setValue(v)
                dlg.vignette_opacity_sld.blockSignals(False)
                dlg._update_vignette_opacity_label(v)
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        if self.chroma.persist:
            self.save_config()

    def _on_opacity(self, v: int):
        # Совместимость со старыми вызовами. В меню ползунка больше нет:
        # непрозрачность теперь живёт только в блоке «Виньетка».
        self.set_window_opacity_percent(v)

    def _on_feather(self, v: int):
        """v13.3: ползунок управляет ТОЛЬКО виньеткой (state.edge_feather).
        Раньше он же двигал chroma.feather через коэффициент — это
        давало непредсказуемый результат: кеинг и виньетка живут в
        разных пространствах (px vs % радиуса), общий ползунок не
        работал визуально. Теперь у каждой мягкости свой ползунок
        в диалоге хромакея."""
        v = int(clamp(v, 0, 100))
        self.state.edge_feather = v
        self._circle_mask_cache.clear()   # сброс кэша при изменении
        # Если открыт диалог хромакея — синхронизируем оба ползунка там
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                for sld, val in ((dlg.vignette_sld, v),
                                  (dlg.feather_sld, self.chroma.feather)):
                    if sld.value() != val:
                        sld.blockSignals(True)
                        sld.setValue(val)
                        sld.blockSignals(False)
                dlg._update_feather_label()
                dlg._update_vignette_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        self.update()
        if self.chroma.persist:
            self.save_config()

    def _sync_chroma_dialog_vignette_controls(self):
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is None:
            return
        try:
            pairs = (
                (dlg.vignette_on_top_chk, bool(self.state.always_on_top)),
                (dlg.vignette_click_through_chk, bool(self.state.click_through)),
                (dlg.vignette_mirror_chk, bool(self.state.window_mirror)),
            )
            for widget, value in pairs:
                if widget.isChecked() != value:
                    widget.blockSignals(True)
                    widget.setChecked(value)
                    widget.blockSignals(False)
            opacity = int(clamp(self.state.window_opacity, 0.2, 1.0) * 100)
            if dlg.vignette_opacity_sld.value() != opacity:
                dlg.vignette_opacity_sld.blockSignals(True)
                dlg.vignette_opacity_sld.setValue(opacity)
                dlg.vignette_opacity_sld.blockSignals(False)
            dlg._update_vignette_opacity_label(opacity)
        except (RuntimeError, AttributeError):
            self._chroma_dlg = None

    # ------------------------------------------------------------------
    # Переключатели состояния
    # ------------------------------------------------------------------
    def set_always_on_top(self, v: bool):
        self.state.always_on_top = v
        self.act_on_top.setChecked(v)
        self._sync_chroma_dialog_vignette_controls()
        flags = self._base_flags | (Qt.WindowStaysOnTopHint if v else 0)
        self.setWindowFlags(flags)
        # setWindowFlags прячет окно — показываем снова только если оно уже было видно
        if self.isVisible():
            self.show()
        _logger.info("always_on_top=%s", v)

    def set_window_mirror(self, v: bool):
        self.state.window_mirror = v
        self.act_mirror.setChecked(v)
        self._sync_chroma_dialog_vignette_controls()

    def set_click_through(self, v: bool):
        self.state.click_through = v
        self.act_click_thru.setChecked(v)
        self._sync_chroma_dialog_vignette_controls()
        self.setAttribute(Qt.WA_TransparentForMouseEvents, v)
        if os.name == "nt":
            WS_EX_LAYERED    = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            GWL_EXSTYLE = -20
            user32 = ctypes.windll.user32
            hwnd = int(self.winId())
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED
            if v: style |= WS_EX_TRANSPARENT
            else: style &= ~WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        if self.isVisible():
            self.show()

    def set_vcam_enabled(self, v: bool):
        if getattr(self, "_shutdown_started", False):
            return
        v = bool(v)
        self.state.vcam_enabled = v
        if self.act_vcam_enable.isChecked() != v:
            self.act_vcam_enable.blockSignals(True)
            self.act_vcam_enable.setChecked(v)
            self.act_vcam_enable.blockSignals(False)
        if v:
            self._ensure_frame_source()
            self._start_vcam()
        else:
            self._stop_vcam()
            self._release_frame_source_if_idle()
        if self.chroma.persist:
            self.save_config()

    def set_vcam_mirror(self, v: bool):
        self.state.vcam_mirror = v
        self.act_vcam_mirror.setChecked(v)

    def set_chroma_enabled(self, v: bool):
        self.chroma.enabled = v
        self.act_chroma.setChecked(v)

    def _current_crop_mode(self) -> str:
        """Три взаимоисключающих режима кропа для окна."""
        if getattr(self.dynamic_crop, "enabled", False):
            return "dynamic"
        if getattr(self.crop, "enabled", False):
            return "manual"
        return "off"

    def _sync_crop_mode_actions(self):
        mode = self._current_crop_mode()
        pairs = (
            (getattr(self, "act_crop_off", None), mode == "off"),
            (getattr(self, "act_crop_manual", None), mode == "manual"),
            (getattr(self, "act_dynamic_crop", None), mode == "dynamic"),
            (getattr(self, "act_crop_enable", None), mode == "manual"),
        )
        for act, checked in pairs:
            if act is None:
                continue
            try:
                if act.isChecked() != checked:
                    act.blockSignals(True)
                    act.setChecked(bool(checked))
                    act.blockSignals(False)
            except RuntimeError:
                pass

        self._sync_dynamic_menu_actions()

        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                if hasattr(dlg, "_sync_crop_mode_radios"):
                    dlg._sync_crop_mode_radios()
                if hasattr(dlg, "_update_crop_label"):
                    dlg._update_crop_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None

    def _sync_dynamic_menu_actions(self):
        act = getattr(self, "act_dynamic_debug", None)
        if act is not None:
            try:
                value = bool(getattr(self.dynamic_crop, "show_debug_view", False))
                if act.isChecked() != value:
                    act.blockSignals(True)
                    act.setChecked(value)
                    act.blockSignals(False)
            except RuntimeError:
                pass

    def set_dynamic_debug_view(self, value: bool):
        self.dynamic_crop.show_debug_view = bool(value)
        self._sync_dynamic_menu_actions()
        if self.chroma.persist:
            self.save_config()

    def set_crop_mode(self, mode: str, save: bool = True):
        """Единая точка переключения: выключен / ручной / динамический.

        Ручной rect сохраняется, но не применяется в режиме dynamic.
        Динамический runtime очищается при выходе из dynamic, чтобы старые
        координаты лица не всплывали после переключений.
        """
        mode = str(mode or "off").lower()
        if mode not in ("off", "manual", "dynamic"):
            mode = "off"

        self.crop.enabled = (mode == "manual")
        new_dynamic = (mode == "dynamic")
        if self.dynamic_crop.enabled != new_dynamic:
            self.dynamic_crop.enabled = new_dynamic
            if not new_dynamic:
                self._dynamic_crop_runtime = DynamicCropRuntimeState()
                self._reset_face_director()

        self._sync_crop_mode_actions()
        self.update()
        if save and self.chroma.persist:
            self.save_config()

    def set_crop_enabled(self, v: bool):
        # Совместимость со старыми QAction/хоткеями.
        self.set_crop_mode("manual" if v else "off")

    def set_dynamic_crop_enabled(self, v: bool, save: bool = True):
        """Совместимость со старым API: теперь это режим кропа."""
        self.set_crop_mode("dynamic" if v else "off", save=save)

    def _set_window_shape(self, shape: str):
        self.state.window_shape = shape
        self.act_shape_circ.setChecked(shape == "circle")
        self.act_shape_sq.setChecked(shape == "square")
        self._update_mask(); self.update()

    # ------------------------------------------------------------------
    # Камера
    # ------------------------------------------------------------------
    def _update_cam_label(self):
        self.act_cam_toggle.setText(
            "Выключить камеру" if (self.cap and self.cap.isOpened())
            else "Включить камеру")

    def toggle_camera(self):
        if self.cap and self.cap.isOpened():
            self._stop_capture_loop(release=True, log=True)
            self._frame_timer.stop()
            _logger.info("Камера выключена")
        else:
            if self._open_camera(self.camera_index):
                self._frame_timer.start(int(1000 / (self.fps or 30)))
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось открыть камеру.")
        self._update_cam_label()

    def _refresh_camera_names(self):
        # Windows FriendlyName нельзя надёжно сопоставить с индексами OpenCV
        # простым zip/sort: порядок PnP-устройств и индексов CAP_DSHOW — разные
        # вещи. Поэтому не показываем пользователю потенциально ложные имена.
        # Для удобства остаются ручные aliases через UI.
        self._windows_camera_names = get_windows_camera_names()
        self.camera_names = {}

    def camera_display_name(self, idx: int, include_props: bool = False) -> str:
        idx = int(idx)
        aliases = getattr(self.state, "camera_aliases", {})
        if not isinstance(aliases, dict):
            aliases = {}
            self.state.camera_aliases = aliases
        base = str(aliases.get(str(idx)) or self.camera_names.get(idx) or f"Камера {idx}")
        if include_props and idx == getattr(self, "camera_index", -1):
            cap = getattr(self, "cap", None)
            if cap is not None and cap.isOpened():
                with getattr(self, "_cap_lock", threading.RLock()):
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                    fps = int(round(cap.get(cv2.CAP_PROP_FPS) or (self.fps or 30)))
                if w > 0 and h > 0:
                    return f"{base} · {w}×{h} · {fps} FPS"
        return base

    def refresh_camera_labels(self):
        for a in getattr(self, "_cam_actions", []):
            try:
                a.setText(self.camera_display_name(int(a.data()), include_props=False))
            except Exception:
                pass
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._reload_camera_combo()
                dlg._update_camera_status()
            except Exception:
                pass

    def switch_camera(self, index: int):
        if index == self.camera_index:
            return
        old_index = self.camera_index
        was_active = self._frame_timer.isActive()
        self._stop_capture_loop(release=True, log=False)
        self.camera_index = index
        if self._open_camera(index):
            for a in self._cam_actions:
                a.setChecked(int(a.data()) == index)
            if was_active:
                self._frame_timer.start(int(1000 / (self.fps or 30)))
            self.state.camera_index = int(index)
            self.save_config()
            _logger.info("Камера переключена: %s → %s", old_index, index)
        else:
            # Откат на старую камеру
            _logger.error("Не удалось открыть камеру %s, откат на %s", index, old_index)
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть камеру {index}")
            self.camera_index = old_index
            self._open_camera(old_index)
            for a in self._cam_actions:
                a.setChecked(int(a.data()) == old_index)

    def refresh_cameras(self):
        """Пересканирует доступные камеры и пересобирает подменю «Камера».
        Полезно, когда виртуальная камера (OBS/любая другая) включена
        уже после старта программы — она не появится в списке без
        повторного сканирования."""
        old_list = list(self.available_cameras)
        new_list = find_cameras(skip_index=self.camera_index)
        # find_cameras пропускает уже открытый индекс — добавим его сами,
        # чтобы он остался в подменю
        if self.camera_index not in new_list:
            new_list = [self.camera_index] + new_list
        new_list = sorted(set(new_list))
        if new_list == sorted(old_list) + ([self.camera_index]
                if self.camera_index not in old_list else []):
            new_list_check = sorted(set(old_list) | {self.camera_index})
        else:
            new_list_check = new_list
        if new_list_check == sorted(set(old_list) | {self.camera_index}):
            self._refresh_camera_names()
            self.refresh_camera_labels()
            QMessageBox.information(
                self, "Список камер",
                f"Найдено камер: {len(new_list_check)} (изменений нет).")
            return
        self.available_cameras = new_list_check
        self._refresh_camera_names()
        # Пересобираем _cam_actions (старые QAction-ы удаляем)
        for a in self._cam_actions:
            try:
                self._cam_group.removeAction(a)
                a.deleteLater()
            except Exception: pass
        self._cam_actions = []
        for idx in self.available_cameras:
            a = QAction(self.camera_display_name(idx, include_props=False), self, checkable=True)
            a.setData(int(idx))
            a.setChecked(idx == self.camera_index)
            a.triggered.connect(lambda _, i=idx: self.switch_camera(i))
            self._cam_group.addAction(a)
            self._cam_actions.append(a)
        # Перезаполняем оба меню «Окно»: удаляем всё после якорного
        # сепаратора (камеры + кнопка «Обновить»), вставляем заново.
        for win_m, anchor in (
            (getattr(self, "_ctx_win_menu",  None), getattr(self, "_ctx_cam_anchor",  None)),
            (getattr(self, "_tray_win_menu", None), getattr(self, "_tray_cam_anchor", None)),
        ):
            if win_m is None or anchor is None:
                continue
            actions = win_m.actions()
            try:
                idx0 = actions.index(anchor) + 1
            except ValueError:
                continue
            # Удаляем всё после якоря
            for old_a in actions[idx0:]:
                win_m.removeAction(old_a)
            # Добавляем актуальный список + «Обновить»
            for a in self._cam_actions:
                win_m.addAction(a)
            win_m.addAction(self.act_cam_refresh)
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._reload_camera_combo()
                dlg._update_camera_status()
            except Exception:
                pass
        _logger.info("Список камер обновлён: %s", self.available_cameras)
        QMessageBox.information(
            self, "Готово",
            f"Найдено камер: {len(self.available_cameras)}.")

    # ------------------------------------------------------------------
    # Источник кадров
    # ------------------------------------------------------------------
    def _ensure_frame_source(self) -> bool:
        """Открывает физическую камеру и таймер кадров, если они нужны.

        Источник кадров нужен в двух независимых случаях:
          1) плавающее окно показано;
          2) включена виртуальная камера.
        Поэтому скрытие окна больше не выключает vcam.
        """
        if getattr(self, "_shutdown_started", False):
            return False
        opened = bool(self.cap and self.cap.isOpened())
        if not opened:
            opened = self._open_camera(self.camera_index)
        if opened and not self._frame_timer.isActive():
            self._frame_timer.start(int(1000 / (self.fps or 30)))
        if opened and getattr(self, "_capture_loop", None) is not None and not self._capture_loop.is_running():
            self._capture_loop.set_capture(self.cap, int(self.camera_index), int(self.fps or 30))
        self._update_cam_label()
        return opened

    def _release_frame_source_if_idle(self):
        """Освобождает физическую камеру только если нет окна и vcam."""
        if getattr(self, "_shutdown_started", False):
            return
        if self.isVisible() or self.state.vcam_enabled:
            return
        try:
            if self._frame_timer.isActive():
                self._frame_timer.stop()
        except Exception:
            pass
        self._stop_capture_loop(release=True, log=False)
        _logger.info("Физическая камера освобождена: окно скрыто, vcam выключена")
        self._update_cam_label()

    # ------------------------------------------------------------------
    # Показ/скрытие окна из трея
    # ------------------------------------------------------------------
    def _on_tray_show(self, checked: bool):
        if getattr(self, "_shutdown_started", False):
            return
        if checked:
            flags = self._base_flags | (Qt.WindowStaysOnTopHint if self.state.always_on_top else 0)
            self.setWindowFlags(flags)
            self.show(); self.raise_(); self.activateWindow()
            self._ensure_frame_source()
            if self.state.vcam_enabled:
                self._start_vcam()
        else:
            self.hide()
            self._release_frame_source_if_idle()
        self._update_cam_label()

    # ------------------------------------------------------------------
    # Виртуальная камера
    # ------------------------------------------------------------------
    def _start_vcam(self):
        if getattr(self, "_shutdown_started", False):
            return
        if not HAVE_PYVIRTUALCAM:
            QMessageBox.warning(self, "pyvirtualcam не установлен",
                                "Установите pyvirtualcam и драйвер.")
            self.state.vcam_enabled = False
            self.act_vcam_enable.setChecked(False)
            return
        if self.vcam is None:
            if not (self.cap and self.cap.isOpened()):
                self._ensure_frame_source()
            if self.last_frame_bgr is None and self._pending_frame_bgr is not None:
                self.last_frame_bgr = self._pending_frame_bgr
            # Если разрешение не задано через --vcam-res, берём фактическое
            # из последнего полученного кадра. v13.3: в режиме
            # passthrough_native ОБЯЗАТЕЛЬНО берём из реального кадра,
            # игнорируя override — иначе теряется смысл «как с
            # физической камеры».
            need_native = self.state.vcam_passthrough_native
            if need_native or not self.vcam_res_override:
                if self.last_frame_bgr is not None:
                    h, w = self.last_frame_bgr.shape[:2]
                    self.vcam_w, self.vcam_h = w, h
                else:
                    # Кадра ещё нет — возьмём разумный дефолт
                    self.vcam_w, self.vcam_h = 1280, 720
            try:
                self.vcam = pyvirtualcam.Camera(
                    width=self.vcam_w, height=self.vcam_h,
                    fps=self.fps or 30, print_fps=False)
                _logger.info("Виртуальная камера %dx%d @%s",
                             self.vcam_w, self.vcam_h, self.fps or 30)
            except Exception as e:
                _log_exc("Ошибка запуска виртуальной камеры", e)
                QMessageBox.critical(self, "Ошибка", f"Виртуальная камера:\n{e}")
                self.vcam = None
                self.state.vcam_enabled = False
                self.act_vcam_enable.setChecked(False)

    def _stop_vcam(self):
        if self.vcam is not None:
            cam = self.vcam
            self.vcam = None
            try:
                cam.close()
            except Exception as e:
                _log_exc("Ошибка остановки vcam", e)
            try:
                del cam
            except Exception:
                pass
            _logger.info("Виртуальная камера остановлена")

    # ------------------------------------------------------------------
    # PTZ: физическое подруливание камеры
    # ------------------------------------------------------------------
    def _ptz_prop(self, axis: str):
        mapping = {
            "pan": getattr(cv2, "CAP_PROP_PAN", 33),
            "tilt": getattr(cv2, "CAP_PROP_TILT", 34),
            "zoom": getattr(cv2, "CAP_PROP_ZOOM", 27),
        }
        return mapping.get(axis)

    def _ptz_step_value(self, axis: str) -> float:
        cfg = self.ptz
        if axis == "pan":
            return float(getattr(cfg, "pan_step", 1.0))
        if axis == "tilt":
            return float(getattr(cfg, "tilt_step", 1.0))
        return float(getattr(cfg, "zoom_step", 1.0))

    def _ptz_adjust(self, axis: str, direction: int, reason: str = "auto") -> bool:
        cap = getattr(self, "cap", None)
        if cap is None or not cap.isOpened():
            self._ptz_runtime.last_error = "камера не открыта"
            return False
        prop = self._ptz_prop(axis)
        if prop is None:
            self._ptz_runtime.last_error = f"нет свойства {axis}"
            return False

        cfg = self.ptz
        if axis == "pan" and bool(getattr(cfg, "invert_pan", False)):
            direction = -direction
        elif axis == "tilt" and bool(getattr(cfg, "invert_tilt", False)):
            direction = -direction
        elif axis == "zoom" and bool(getattr(cfg, "invert_zoom", False)):
            direction = -direction

        step = float(self._ptz_step_value(axis))

        command_attr = f"command_{axis}"
        stored_command = getattr(self._ptz_runtime, command_attr, None)

        current = None
        try:
            with getattr(self, "_cap_lock", threading.RLock()):
                raw_current = float(cap.get(prop))
            if np.isfinite(raw_current):
                current = raw_current
        except Exception:
            current = None

        # Важное отличие v10: если уже есть накопленная команда, считаем от неё,
        # а не от cap.get(). У многих DirectShow-драйверов cap.get() врёт: всегда
        # возвращает 0 или старое значение. Тогда v9 каждый раз слал один и тот же
        # target и камера визуально не двигалась. Великолепная API-ловушка, куда же без неё.
        if stored_command is not None and np.isfinite(float(stored_command)):
            base = float(stored_command)
        elif current is not None:
            base = float(current)
        else:
            base = 0.0

        target = base + float(direction) * step
        try:
            with getattr(self, "_cap_lock", threading.RLock()):
                ok = bool(cap.set(prop, float(target)))
        except Exception as e:
            self._ptz_runtime.last_error = f"{axis}: {e}"
            return False

        setattr(self._ptz_runtime, command_attr, float(target))
        attr = f"last_{axis}"
        if hasattr(self._ptz_runtime, attr):
            setattr(self._ptz_runtime, attr, float(target))

        current_txt = "?" if current is None else f"{current:.2f}"
        self._ptz_runtime.last_command = (
            f"{axis} {direction:+d} · {reason} · {current_txt}→{target:.2f}"
            if ok else
            f"{axis}: команда не принята драйвером · {current_txt}→{target:.2f}"
        )
        if not ok:
            self._ptz_runtime.last_error = self._ptz_runtime.last_command
        else:
            self._ptz_runtime.last_error = ""
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                if hasattr(dlg, "_sync_ptz_position_sliders"):
                    dlg._sync_ptz_position_sliders(read_camera=False)
                else:
                    dlg._update_ptz_status()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        return ok

    def _ptz_pan(self, direction: int, reason: str = "auto") -> bool:
        return self._ptz_adjust("pan", int(direction), reason=reason)

    def _ptz_tilt(self, direction: int, reason: str = "auto") -> bool:
        return self._ptz_adjust("tilt", int(direction), reason=reason)

    def _ptz_zoom(self, direction: int, reason: str = "auto") -> bool:
        return self._ptz_adjust("zoom", int(direction), reason=reason)

    def _ptz_read_axis(self, axis: str) -> float | None:
        cap = getattr(self, "cap", None)
        prop = self._ptz_prop(axis)
        if cap is None or not cap.isOpened() or prop is None:
            return None
        try:
            with getattr(self, "_cap_lock", threading.RLock()):
                value = float(cap.get(prop))
        except Exception:
            return None
        if not np.isfinite(value):
            return None
        command_attr = f"command_{axis}"
        if hasattr(self._ptz_runtime, command_attr):
            setattr(self._ptz_runtime, command_attr, float(value))
        return value

    def _ptz_set_axis_absolute(self, axis: str, value: float | None, reason: str = "home") -> bool:
        if value is None:
            return True
        cap = getattr(self, "cap", None)
        prop = self._ptz_prop(axis)
        if cap is None or not cap.isOpened() or prop is None:
            self._ptz_runtime.last_error = f"{axis}: камера/свойство недоступно"
            return False
        try:
            with getattr(self, "_cap_lock", threading.RLock()):
                ok = bool(cap.set(prop, float(value)))
        except Exception as e:
            self._ptz_runtime.last_error = f"{axis}: {e}"
            return False
        command_attr = f"command_{axis}"
        if hasattr(self._ptz_runtime, command_attr):
            setattr(self._ptz_runtime, command_attr, float(value))
        attr = f"last_{axis}"
        if hasattr(self._ptz_runtime, attr):
            setattr(self._ptz_runtime, attr, float(value))
        self._ptz_runtime.last_command = f"{axis}={float(value):.2f} · {reason}" if ok else f"{axis}: команда не принята драйвером"
        if ok:
            self._ptz_runtime.last_error = ""
        else:
            self._ptz_runtime.last_error = self._ptz_runtime.last_command
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                if hasattr(dlg, "_sync_ptz_position_sliders"):
                    dlg._sync_ptz_position_sliders(read_camera=False)
                else:
                    dlg._update_ptz_status()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        return ok

    def _sync_dynamic_settings_dialog(self):
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                if hasattr(dlg, "_load_dynamic_from_owner"):
                    dlg._load_dynamic_from_owner()
                if hasattr(dlg, "_sync_ptz_position_sliders"):
                    dlg._sync_ptz_position_sliders(read_camera=False)
                elif hasattr(dlg, "_update_ptz_status"):
                    dlg._update_ptz_status()
                if hasattr(dlg, "_update_crop_label"):
                    dlg._update_crop_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None

    def _ptz_remember_home(self):
        """Запоминает базовое положение физической камеры и цели окна."""
        cfg = self.ptz
        cfg.home_pan = self._ptz_read_axis("pan")
        cfg.home_tilt = self._ptz_read_axis("tilt")
        cfg.home_zoom = self._ptz_read_axis("zoom")

        dcfg = self.dynamic_crop
        cfg.home_offset_x = float(getattr(dcfg, "offset_x", 0.0))
        cfg.home_offset_y = float(getattr(dcfg, "offset_y", -0.05))
        cfg.home_circle_offset_x = float(getattr(dcfg, "circle_offset_x", 0.0))
        cfg.home_circle_offset_y = float(getattr(dcfg, "circle_offset_y", 0.0))

        self._ptz_runtime.last_command = "база сохранена"
        self._ptz_runtime.last_error = ""
        self._sync_dynamic_settings_dialog()
        if self.chroma.persist:
            self.save_config()

    def _reset_camera_and_target_to_home(self):
        """Клавиша 0: вернуть физические повороты камеры и цель окна к базе."""
        cfg = self.ptz
        ok_pan = self._ptz_set_axis_absolute("pan", getattr(cfg, "home_pan", None), reason="home")
        ok_tilt = self._ptz_set_axis_absolute("tilt", getattr(cfg, "home_tilt", None), reason="home")
        ok_zoom = self._ptz_set_axis_absolute("zoom", getattr(cfg, "home_zoom", None), reason="home")

        max_offset = float(getattr(self.dynamic_crop, "max_composition_offset", MAX_COMPOSITION_OFFSET))
        self.dynamic_crop.offset_x = float(clamp(getattr(cfg, "home_offset_x", 0.0), -max_offset, max_offset))
        self.dynamic_crop.offset_y = float(clamp(getattr(cfg, "home_offset_y", -0.05), -max_offset, max_offset))
        self.dynamic_crop.circle_offset_x = float(clamp(getattr(cfg, "home_circle_offset_x", 0.0), -max_offset, max_offset))
        self.dynamic_crop.circle_offset_y = float(clamp(getattr(cfg, "home_circle_offset_y", 0.0), -max_offset, max_offset))
        self._dynamic_crop_runtime = DynamicCropRuntimeState()
        self._reset_face_director()

        if ok_pan and ok_tilt and ok_zoom:
            self._ptz_runtime.last_command = "камера и цель возвращены к базе"
            self._ptz_runtime.last_error = ""
        else:
            self._ptz_runtime.last_command = "цель возвращена, часть PTZ-команд не принята"
        self._sync_dynamic_settings_dialog()
        if self.chroma.persist:
            self.save_config()

    def _ptz_process_dynamic_tracking(self, frame: np.ndarray, runtime: DynamicCropRuntimeState):
        cfg = getattr(self, "ptz", PTZConfig())
        if not bool(getattr(cfg, "enabled", False)):
            return
        if frame is None or runtime is None:
            return

        if self._ptz_runtime.cooldown > 0:
            self._ptz_runtime.cooldown -= 1
            return

        h, w = frame.shape[:2]
        if h <= 1 or w <= 1:
            return

        pan_dir = 0
        tilt_dir = 0
        reasons = []

        rect = runtime.crop_rect
        face = runtime.face

        # Триггер 1: динамический кроп упёрся в запас края исходного изображения.
        # Это главный сигнал: программному кропу уже некуда брать сцену, пора
        # двигать физическую камеру.
        if bool(getattr(cfg, "trigger_edge_guard", True)) and rect:
            margin_ratio = clamp(float(getattr(cfg, "edge_guard_percent", 10)) / 100.0, 0.0, 0.30)
            margin_x = float(w) * margin_ratio
            margin_y = float(h) * margin_ratio
            x, y, rw, rh = [float(v) for v in rect]

            touches_left = x <= margin_x
            touches_right = x + rw >= float(w) - margin_x
            touches_top = y <= margin_y
            touches_bottom = y + rh >= float(h) - margin_y

            if touches_left and touches_right and face is not None:
                # Кроп шире безопасной зоны: выбираем направление по положению лица.
                if face.cx < w * 0.47:
                    pan_dir = -1; reasons.append("edge wide left")
                elif face.cx > w * 0.53:
                    pan_dir = 1; reasons.append("edge wide right")
            elif touches_left:
                pan_dir = -1; reasons.append("left edge")
            elif touches_right:
                pan_dir = 1; reasons.append("right edge")

            if touches_top and touches_bottom and face is not None:
                if face.cy < h * 0.47:
                    tilt_dir = -1; reasons.append("edge wide top")
                elif face.cy > h * 0.53:
                    tilt_dir = 1; reasons.append("edge wide bottom")
            elif touches_top:
                tilt_dir = -1; reasons.append("top edge")
            elif touches_bottom:
                tilt_dir = 1; reasons.append("bottom edge")

        # Триггер 2: фокусная точка лица ушла в верхнюю/нижнюю треть кадра.
        # Используем фактический центр лица, а не центр crop-а: crop может держать
        # красивую картинку программно, но физическая камера всё ещё смотрит не туда.
        if bool(getattr(cfg, "trigger_focus_vertical_thirds", True)) and face is not None:
            third = clamp(float(getattr(cfg, "focus_third_percent", 33)) / 100.0, 0.20, 0.45)
            fy = float(face.cy)
            if fy <= h * third:
                tilt_dir = -1; reasons.append("focus top third")
            elif fy >= h * (1.0 - third):
                tilt_dir = 1; reasons.append("focus bottom third")

        if not reasons:
            self._ptz_runtime.last_trigger = ""
            return

        reason_text = ", ".join(reasons)
        self._ptz_runtime.last_trigger = reason_text

        attempted = False
        issued = False
        # За один тик даём максимум две команды: pan и tilt. Очереди не плодим.
        if pan_dir < 0:
            attempted = True
            issued = self._ptz_pan(-1, reason=reason_text) or issued
        elif pan_dir > 0:
            attempted = True
            issued = self._ptz_pan(1, reason=reason_text) or issued
        if tilt_dir < 0:
            attempted = True
            issued = self._ptz_tilt(-1, reason=reason_text) or issued
        elif tilt_dir > 0:
            attempted = True
            issued = self._ptz_tilt(1, reason=reason_text) or issued

        # Cooldown ставим даже при отказе драйвера, иначе будем долбить CAP_PROP
        # каждый кадр и тормозить весь видеоконтур. Спасибо, Windows, очень мило.
        if attempted:
            self._ptz_runtime.cooldown = int(clamp(getattr(cfg, "cooldown_frames", 8), 1, 60))
            if not issued and not getattr(self._ptz_runtime, "last_error", ""):
                self._ptz_runtime.last_error = f"PTZ-триггер есть, команда не выполнена: {reason_text}"

    # ------------------------------------------------------------------
    # Модуль автокомпозиции лица
    # ------------------------------------------------------------------
    def _reset_face_director(self):
        director = getattr(self, "_face_director", None)
        if director is not None:
            try:
                director.reset()
            except Exception as e:
                _log_exc("FaceAutoDirector: ошибка reset", e)

    def _face_director_config(self):
        if not HAVE_FACE_DIRECTOR or FaceDirectorConfig is None:
            return None
        cfg = self.dynamic_crop
        return FaceDirectorConfig(
            enabled=bool(getattr(cfg, "enabled", False)),
            detector=str(getattr(cfg, "detector", "mediapipe")),
            analysis_scale_percent=int(getattr(cfg, "analysis_scale_percent", 25)),
            min_face_size_full_frame=int(getattr(cfg, "min_face_size_full_frame", MIN_FACE_SIZE_FULL_FRAME)),
            smoothing=float(getattr(cfg, "position_smoothing", getattr(cfg, "smoothing", DEFAULT_SMOOTHING))),
            position_smoothing=float(getattr(cfg, "position_smoothing", getattr(cfg, "smoothing", DEFAULT_SMOOTHING))),
            scale_smoothing=float(getattr(cfg, "scale_smoothing", 0.22)),
            center_dead_zone=float(getattr(cfg, "position_dead_zone", getattr(cfg, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE))),
            position_dead_zone=float(getattr(cfg, "position_dead_zone", getattr(cfg, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE))),
            scale_dead_zone=float(getattr(cfg, "scale_dead_zone", 0.08)),
            tracking_mode=str(getattr(cfg, "tracking_mode", "eyes_ipd") or "eyes_ipd"),
            circle_to_head=float(getattr(cfg, "circle_to_head", DYNAMIC_CROP_MIN_CIRCLE_TO_HEAD)),
            crop_padding=float(getattr(cfg, "crop_padding", DEFAULT_DYNAMIC_CROP_PADDING)),
            offset_x=float(getattr(cfg, "offset_x", 0.0)),
            offset_y=float(getattr(cfg, "offset_y", -0.05)),
            circle_offset_x=float(getattr(cfg, "circle_offset_x", 0.0)),
            circle_offset_y=float(getattr(cfg, "circle_offset_y", 0.0)),
            return_speed=float(getattr(cfg, "return_speed", DEFAULT_DYNAMIC_RETURN_SPEED)),
            show_debug_view=bool(getattr(cfg, "show_debug_view", False)),
            fast_roi_tracking=bool(getattr(cfg, "fast_roi_tracking", True)),
            face_roi_margin=float(getattr(cfg, "face_roi_margin", 2.8)),
            detector_min_neighbors=int(getattr(cfg, "detector_min_neighbors", 4)),
            return_after_lost_frames=int(globals().get("DYNAMIC_CROP_RETURN_AFTER_LOST_FRAMES", 18)),
        )

    def _sync_dynamic_runtime_from_director(self, result):
        runtime = self._dynamic_crop_runtime

        def box_to_dynamic_box(box):
            if box is None:
                return None
            return DynamicBox(float(box.x), float(box.y), float(box.w), float(box.h))

        def circle_to_dynamic_circle(circle):
            if circle is None:
                return None
            return DynamicCircleState(float(circle.cx), float(circle.cy), float(circle.diameter))

        runtime.raw_face = box_to_dynamic_box(getattr(result, "raw_face", None))
        runtime.previous_face = box_to_dynamic_box(getattr(result, "raw_face", None))
        runtime.face = box_to_dynamic_box(getattr(result, "face", None))
        runtime.circle = circle_to_dynamic_circle(getattr(result, "circle", None))
        runtime.target_circle = circle_to_dynamic_circle(getattr(result, "target_circle", None))
        runtime.stable_circle = circle_to_dynamic_circle(getattr(result, "stable_circle", None))
        rect = getattr(result, "crop_rect", None)
        runtime.crop_rect = [int(v) for v in rect] if rect is not None else None
        runtime.face_found = bool(getattr(result, "face_found", False))
        runtime.lost_frames = int(getattr(result, "lost_frames", 0))
        runtime.processed_frames = int(getattr(result, "processed_frames", runtime.processed_frames + 1))

    def _face_director_crop_source(self, frame: np.ndarray) -> np.ndarray | None:
        director = getattr(self, "_face_director", None)
        if not HAVE_FACE_DIRECTOR or director is None:
            return None
        cfg = self._face_director_config()
        if cfg is None:
            return None
        try:
            result = director.process(frame, cfg)
            self._face_director_last_result = result
            self._sync_dynamic_runtime_from_director(result)
            self._ptz_process_dynamic_tracking(frame, self._dynamic_crop_runtime)
            if getattr(result, "debug_bgr", None) is not None:
                return result.debug_bgr
            return getattr(result, "crop_bgr", None)
        except Exception as e:
            _log_exc("FaceAutoDirector: ошибка обработки кадра", e)
            # Если внешний модуль упал, ниже остаётся штатный legacy-контур.
            return None

    # ------------------------------------------------------------------
    # Динамический кроп / автокомпозиция
    # ------------------------------------------------------------------
    def _ensure_dynamic_face_detector(self):
        if self._dynamic_face_detector is False:
            return None
        if self._dynamic_face_detector is not None:
            return self._dynamic_face_detector
        try:
            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            detector = cv2.CascadeClassifier(path)
            if detector.empty():
                _logger.warning("Динамический кроп: не загружен Haar Cascade: %s", path)
                self._dynamic_face_detector = False
                return None
            self._dynamic_face_detector = detector
            return detector
        except Exception as e:
            _log_exc("Динамический кроп: ошибка загрузки детектора", e)
            self._dynamic_face_detector = False
            return None

    def _dynamic_choose_best_face(self, faces, previous_face: DynamicBox | None) -> DynamicBox | None:
        if len(faces) == 0:
            return None
        boxes = [DynamicBox(float(x), float(y), float(w), float(h)) for x, y, w, h in faces]
        if previous_face is None:
            return max(boxes, key=lambda b: b.w * b.h)

        def score(b: DynamicBox) -> float:
            dist = hypot(b.cx - previous_face.cx, b.cy - previous_face.cy)
            area_bonus = 0.001 * b.w * b.h
            return dist - area_bonus

        return min(boxes, key=score)

    def _dynamic_detect_face(self, frame: np.ndarray) -> DynamicBox | None:
        """Быстрая детекция лица для динамического кропа.

        В v8 детектор каждый кадр смотрел весь кадр. На живой камере это
        легко превращалось в слайдшоу: Haar Cascade не обязан быть милым.
        Здесь сначала ищем в ROI вокруг последней цели, и только при промахе
        делаем полный поиск по кадру.
        """
        detector = self._ensure_dynamic_face_detector()
        if detector is None or frame is None:
            return None

        cfg = self.dynamic_crop
        runtime = self._dynamic_crop_runtime
        runtime.processed_frames += 1

        scale_percent = clamp(float(cfg.analysis_scale_percent),
                              DYNAMIC_CROP_ANALYSIS_MIN,
                              DYNAMIC_CROP_ANALYSIS_MAX)
        scale_factor = scale_percent / 100.0
        min_neighbors = int(clamp(int(getattr(cfg, "detector_min_neighbors", 4)), 3, 8))
        min_face_full = max(24, int(getattr(cfg, "min_face_size_full_frame", MIN_FACE_SIZE_FULL_FRAME)))

        def detect_in_region(region: np.ndarray, x0: int, y0: int,
                             previous_full: DynamicBox | None) -> DynamicBox | None:
            if region is None or region.size == 0:
                return None

            if scale_factor < 0.999:
                small = cv2.resize(region, None, fx=scale_factor, fy=scale_factor,
                                   interpolation=cv2.INTER_AREA)
            else:
                small = region

            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            min_face = max(18, int(min_face_full * scale_factor))

            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.08,
                minNeighbors=min_neighbors,
                minSize=(min_face, min_face),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

            previous_small = None
            if previous_full is not None:
                previous_small = DynamicBox(
                    (previous_full.x - x0) * scale_factor,
                    (previous_full.y - y0) * scale_factor,
                    previous_full.w * scale_factor,
                    previous_full.h * scale_factor,
                )

            detected_small = self._dynamic_choose_best_face(faces, previous_small)
            if detected_small is None:
                return None
            return DynamicBox(
                x0 + detected_small.x / scale_factor,
                y0 + detected_small.y / scale_factor,
                detected_small.w / scale_factor,
                detected_small.h / scale_factor,
            )

        h, w = frame.shape[:2]
        previous = runtime.previous_face or runtime.raw_face or runtime.face

        if bool(getattr(cfg, "fast_roi_tracking", True)) and previous is not None and runtime.lost_frames < 20:
            margin = clamp(float(getattr(cfg, "face_roi_margin", 2.8)), 1.4, 6.0)
            side = max(previous.w, previous.h, float(min_face_full)) * margin
            x1 = int(round(previous.cx - side / 2.0))
            y1 = int(round(previous.cy - side / 2.0))
            x2 = int(round(previous.cx + side / 2.0))
            y2 = int(round(previous.cy + side / 2.0))
            x1 = int(clamp(x1, 0, max(0, w - 1)))
            y1 = int(clamp(y1, 0, max(0, h - 1)))
            x2 = int(clamp(x2, x1 + 1, w))
            y2 = int(clamp(y2, y1 + 1, h))
            roi = frame[y1:y2, x1:x2]
            found = detect_in_region(roi, x1, y1, previous)
            if found is not None:
                return found

        return detect_in_region(frame, 0, 0, previous)

    def _dynamic_circle_from_face(self, face: DynamicBox) -> DynamicCircleState:
        cfg = self.dynamic_crop
        diameter = max(40.0, face.size * float(cfg.circle_to_head))
        cx = (face.cx
              - float(getattr(cfg, "offset_x", 0.0)) * diameter
              + float(getattr(cfg, "circle_offset_x", 0.0)) * diameter)
        cy = (face.cy
              - float(getattr(cfg, "offset_y", -0.05)) * diameter
              + float(getattr(cfg, "circle_offset_y", 0.0)) * diameter)
        return DynamicCircleState(cx, cy, diameter)

    def _dynamic_crop_rect_from_circle(self, circle: DynamicCircleState) -> list:
        side = max(80, int(round(circle.diameter * float(getattr(self.dynamic_crop, "crop_padding", DYNAMIC_CROP_PADDING)))))
        x1 = int(round(circle.cx - side / 2.0))
        y1 = int(round(circle.cy - side / 2.0))
        return [x1, y1, side, side]


    def _dynamic_inner_circle_scale(self) -> float | None:
        """Возвращает отношение внутреннего композиционного круга к crop_rect.

        dynamic crop deliberately keeps crop_rect larger than the actual
        visible circle: crop_rect = circle.diameter * crop_padding.
        Виньетка должна строиться по внутреннему circle.diameter, а не по
        запасному crop_rect. Иначе видимый круг становится равен запасу,
        а не композиционному кругу, что и давало чёрные поля по краям.
        """
        if not bool(getattr(self.dynamic_crop, "enabled", False)):
            return None
        runtime = getattr(self, "_dynamic_crop_runtime", None)
        circle = getattr(runtime, "circle", None)
        rect = getattr(runtime, "crop_rect", None)
        try:
            if circle is not None and rect:
                side = max(float(rect[2]), float(rect[3]), 1.0)
                return float(clamp(float(circle.diameter) / side, 0.05, 1.0))
        except Exception:
            pass
        padding = float(getattr(self.dynamic_crop, "crop_padding", DEFAULT_DYNAMIC_CROP_PADDING))
        if padding <= 0:
            return 1.0
        return float(clamp(1.0 / padding, 0.05, 1.0))

    def _crop_alpha_with_padding(self, frame: np.ndarray, rect: list) -> np.ndarray | None:
        """Альфа для crop_rect с паддингом.

        Там, где crop_rect выходит за границы физического кадра, BGR-данные
        технически паддятся чёрным. Эта маска делает такие зоны прозрачными,
        чтобы чёрный цвет не превращался в видимый край виньетки.
        """
        if frame is None or rect is None:
            return None
        h, w = frame.shape[:2]
        x1, y1, rw, rh = [int(v) for v in rect]
        rw = max(1, rw)
        rh = max(1, rh)
        x2 = x1 + rw
        y2 = y1 + rh

        ix1 = max(0, x1)
        iy1 = max(0, y1)
        ix2 = min(w, x2)
        iy2 = min(h, y2)

        alpha = np.zeros((rh, rw), dtype=np.uint8)
        if ix2 <= ix1 or iy2 <= iy1:
            return alpha

        dx1 = ix1 - x1
        dy1 = iy1 - y1
        dx2 = dx1 + (ix2 - ix1)
        dy2 = dy1 + (iy2 - iy1)
        alpha[dy1:dy2, dx1:dx2] = 255
        return alpha

    def _dynamic_crop_alpha_for_window(self, frame: np.ndarray) -> np.ndarray | None:
        if frame is None or not bool(getattr(self.dynamic_crop, "enabled", False)):
            return None
        runtime = getattr(self, "_dynamic_crop_runtime", None)
        rect = getattr(runtime, "crop_rect", None)
        if not rect:
            return None
        return self._crop_alpha_with_padding(frame, rect)

    def _fit_square_with_optional_alpha(self, bgr: np.ndarray, target: int,
                                        alpha: np.ndarray | None = None,
                                        mirror: bool = False) -> tuple[np.ndarray, np.ndarray | None]:
        """Fit/center-crop BGR and optional alpha into target×target canvas."""
        if bgr is None:
            return bgr, alpha
        target = max(1, int(target))
        disp = cv2.flip(bgr, 1) if mirror else bgr
        alpha_disp = None
        if alpha is not None:
            alpha_disp = cv2.flip(alpha, 1) if mirror else alpha

        h, w = disp.shape[:2]
        scale = max(target / max(1, w), target / max(1, h))
        nw, nh = max(1, int(ceil(w * scale))), max(1, int(ceil(h * scale)))

        rs = cv2.resize(disp, (nw, nh), interpolation=cv2.INTER_LINEAR)
        rsa = None
        if alpha_disp is not None:
            rsa = cv2.resize(alpha_disp, (nw, nh), interpolation=cv2.INTER_LINEAR)

        sx = max(0, (rs.shape[1] - target) // 2)
        sy = max(0, (rs.shape[0] - target) // 2)
        roi = rs[sy:sy + target, sx:sx + target].copy()
        roi_alpha = rsa[sy:sy + target, sx:sx + target].copy() if rsa is not None else None

        if roi.shape[0] != target or roi.shape[1] != target:
            pad = np.zeros((target, target, 3), dtype=roi.dtype)
            pad[:roi.shape[0], :roi.shape[1]] = roi
            roi = pad
            if roi_alpha is not None:
                apad = np.zeros((target, target), dtype=roi_alpha.dtype)
                apad[:roi_alpha.shape[0], :roi_alpha.shape[1]] = roi_alpha
                roi_alpha = apad

        return roi, roi_alpha

    def _window_visible_circle_size(self, roi: np.ndarray) -> tuple[int, bool]:
        """Returns visible circle diameter and whether content should be shrunk.

        For dynamic crop, visible circle = internal circle.diameter mapped
        into the current crop canvas. Content is already larger because of
        crop_padding, so additional shrink would double-count the reserve.
        """
        base = min(roi.shape[:2])
        inner_scale = self._dynamic_inner_circle_scale()
        if inner_scale is not None:
            return max(1, int(round(base * inner_scale))), False

        content_scale = clamp(
            getattr(self.state, "window_content_scale",
                    int(WINDOW_CIRCLE_CONTENT_SCALE_DEFAULT * 100)) / 100.0,
            0.70, 1.00)
        return max(1, int(round(base * content_scale))), bool(content_scale < 1.0)

    def _crop_rect_with_padding(self, frame: np.ndarray, rect: list) -> np.ndarray | None:
        if frame is None or rect is None:
            return None
        h, w = frame.shape[:2]
        x1, y1, rw, rh = [int(v) for v in rect]
        rw = max(1, rw)
        rh = max(1, rh)
        x2 = x1 + rw
        y2 = y1 + rh

        padded = cv2.copyMakeBorder(
            frame,
            top=max(0, -y1),
            bottom=max(0, y2 - h),
            left=max(0, -x1),
            right=max(0, x2 - w),
            borderType=cv2.BORDER_CONSTANT,
            value=(0, 0, 0),
        )
        px1 = x1 + max(0, -x1)
        py1 = y1 + max(0, -y1)
        crop = padded[py1:py1 + rh, px1:px1 + rw]
        if crop.size == 0:
            return None
        return crop.copy()

    def _draw_dynamic_crop_debug(self, crop: np.ndarray, rect: list,
                                 face: DynamicBox | None,
                                 circle: DynamicCircleState | None,
                                 face_found: bool) -> np.ndarray:
        out = crop.copy()
        x1, y1, _rw, _rh = [int(v) for v in rect]

        if circle is not None:
            ccx = int(round(circle.cx - x1))
            ccy = int(round(circle.cy - y1))
            radius = max(1, int(round(circle.diameter / 2.0)))
            cv2.circle(out, (ccx, ccy), radius, (0, 220, 255), 2)
            cv2.line(out, (ccx - 10, ccy), (ccx + 10, ccy), (0, 220, 255), 1)
            cv2.line(out, (ccx, ccy - 10), (ccx, ccy + 10), (0, 220, 255), 1)
            target_face_x, target_face_y = self._dynamic_target_face_point(circle)
            tx = int(round(target_face_x - x1))
            ty = int(round(target_face_y - y1))
            zone = int(round(circle.diameter * clamp(float(getattr(self.dynamic_crop, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE)), 0.0, 0.30)))
            if zone > 0:
                # Мёртвая зона относится к целевой позиции лица внутри круга,
                # а не к геометрическому центру круга. Так кроп не гоняется
                # за пиксельным дрожанием детектора.
                cv2.rectangle(out, (tx - zone, ty - zone), (tx + zone, ty + zone), (120, 120, 120), 1)

            cv2.circle(out, (tx, ty), 6, (255, 180, 80), -1)
            cv2.circle(out, (tx, ty), 12, (255, 180, 80), 1)

        if face is not None:
            fx1 = int(round(face.x - x1))
            fy1 = int(round(face.y - y1))
            fx2 = int(round(face.x + face.w - x1))
            fy2 = int(round(face.y + face.h - y1))
            cv2.rectangle(out, (fx1, fy1), (fx2, fy2), (255, 168, 46), 1)

        status = "FACE" if face_found else "LAST / NO FACE"
        cv2.putText(
            out,
            f"dynamic crop: {status} | head={self.dynamic_crop.circle_to_head:.2f} "
            f"off=({self.dynamic_crop.offset_x:+.2f},{self.dynamic_crop.offset_y:+.2f}) "
            f"zone={getattr(self.dynamic_crop, 'center_dead_zone', DEFAULT_DYNAMIC_CENTER_DEAD_ZONE):.2f} "
            f"analysis={self.dynamic_crop.analysis_scale_percent}%",
            (10, max(24, out.shape[0] - 16)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )
        if bool(getattr(self.ptz, "show_debug", False)):
            msg = getattr(self._ptz_runtime, "last_command", "") or getattr(self._ptz_runtime, "last_error", "") or "PTZ ready"
            cv2.putText(
                out,
                f"ptz: {msg}",
                (10, max(44, out.shape[0] - 36)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (180, 220, 255),
                1,
                cv2.LINE_AA,
            )
        return out

    def _dynamic_smoothing_alpha(self) -> float:
        # Переработанный перенос логики из head_vignette_tracker:
        # состояние идёт через lerp(old, new, k). DEFAULT_SMOOTHING = 0.42
        # ускорен относительно прототипа, но нижняя граница не даёт кропу
        # "залипнуть" при случайном выставлении нуля.
        return float(clamp(float(getattr(self.dynamic_crop, "smoothing", DEFAULT_SMOOTHING)), 0.03, 0.80))

    def _dynamic_smooth_box(self, old: DynamicBox | None, new: DynamicBox) -> DynamicBox:
        if old is None:
            return new
        k = self._dynamic_smoothing_alpha()
        return DynamicBox(
            old.x + (new.x - old.x) * k,
            old.y + (new.y - old.y) * k,
            old.w + (new.w - old.w) * k,
            old.h + (new.h - old.h) * k,
        )

    def _dynamic_smooth_circle(self, old: DynamicCircleState | None, new: DynamicCircleState) -> DynamicCircleState:
        if old is None:
            return new
        k = self._dynamic_smoothing_alpha()
        return DynamicCircleState(
            old.cx + (new.cx - old.cx) * k,
            old.cy + (new.cy - old.cy) * k,
            old.diameter + (new.diameter - old.diameter) * k,
        )

    def _dynamic_target_face_point(self, circle: DynamicCircleState) -> tuple[float, float]:
        """Точка, в которой лицо должно находиться внутри текущего круга."""
        cfg = self.dynamic_crop
        target_x = (
            float(circle.cx)
            + (float(getattr(cfg, "offset_x", 0.0)) - float(getattr(cfg, "circle_offset_x", 0.0))) * float(circle.diameter)
        )
        target_y = (
            float(circle.cy)
            + (float(getattr(cfg, "offset_y", -0.05)) - float(getattr(cfg, "circle_offset_y", 0.0))) * float(circle.diameter)
        )
        return target_x, target_y

    def _dynamic_apply_center_dead_zone(self, current: DynamicCircleState | None,
                                        target: DynamicCircleState,
                                        face: DynamicBox) -> DynamicCircleState:
        """Стабилизирует центр динамического кропа.

        Алгоритм намеренно разделён на три слоя:
        1) face уже сглажен как в head_vignette_tracker;
        2) target_circle рассчитан напрямую из композиции;
        3) current circle двигается только если лицо вышло из зоны вокруг
           своей целевой позиции внутри круга.

        Это не возврат к центру кадра и не привязка к одному пикселю лица.
        Центр crop-а перемещается ровно настолько, чтобы вернуть лицо на
        границу допустимой области, а не гоняться за каждым дрожанием Haar.
        """
        if current is None:
            return target

        zone_ratio = clamp(
            float(getattr(self.dynamic_crop, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE)),
            0.0,
            0.30,
        )
        if zone_ratio <= 0.0:
            return target

        center_limit = max(1.0, float(current.diameter) * zone_ratio)
        desired_face_cx, desired_face_cy = self._dynamic_target_face_point(current)

        dx = float(face.cx - desired_face_cx)
        dy = float(face.cy - desired_face_cy)

        cx = float(current.cx)
        cy = float(current.cy)
        if abs(dx) > center_limit:
            cx += dx - (center_limit if dx > 0 else -center_limit)
        if abs(dy) > center_limit:
            cy += dy - (center_limit if dy > 0 else -center_limit)

        # Haar часто меняет размер рамки на несколько пикселей даже при
        # неподвижной голове. Чтобы кроп не пульсировал, диаметр тоже имеет
        # небольшой порог. Порог связан с той же зоной центра и не требует
        # отдельной настройки в перегруженном меню.
        diameter_limit = max(1.0, float(current.diameter) * zone_ratio * 0.35)
        dd = float(target.diameter - current.diameter)
        diameter = float(current.diameter)
        if abs(dd) > diameter_limit:
            diameter += dd - (diameter_limit if dd > 0 else -diameter_limit)

        return DynamicCircleState(cx, cy, diameter)

    def _dynamic_return_circle_to_frame_center(self, frame: np.ndarray, circle: DynamicCircleState) -> DynamicCircleState:
        speed = clamp(float(getattr(self.dynamic_crop, "return_speed", DEFAULT_DYNAMIC_RETURN_SPEED)), 0.0, 1.0)
        if speed <= 0.0:
            return circle
        h, w = frame.shape[:2]
        return DynamicCircleState(
            circle.cx + (w / 2.0 - circle.cx) * speed,
            circle.cy + (h / 2.0 - circle.cy) * speed,
            circle.diameter,
        )

    def _dynamic_crop_source(self, frame: np.ndarray) -> np.ndarray | None:
        """Возвращает временный crop для плавающего окна.

        База взята из head_vignette_tracker: detect -> previous target ->
        smoothed_face -> target_circle -> smoothed_circle. Переработка для
        КругоЗора: нет cv2.imshow/cv2.waitKeyEx, нет глобального зеркала,
        есть мёртвая зона вокруг композиционной цели лица и сохранение
        последней стабильной области при краткой потере детекции.
        """
        detected_face = self._dynamic_detect_face(frame)
        runtime = self._dynamic_crop_runtime

        if detected_face is not None:
            runtime.raw_face = detected_face
            runtime.previous_face = detected_face
            runtime.lost_frames = 0

            face = self._dynamic_smooth_box(runtime.face, detected_face)
            target_circle = self._dynamic_circle_from_face(face)
            stable_circle = self._dynamic_apply_center_dead_zone(runtime.circle, target_circle, face)
            circle = self._dynamic_smooth_circle(runtime.circle, stable_circle)
            rect = self._dynamic_crop_rect_from_circle(circle)

            runtime.face = face
            runtime.target_circle = target_circle
            runtime.stable_circle = stable_circle
            runtime.circle = circle
            runtime.crop_rect = rect
            runtime.face_found = True
        else:
            runtime.lost_frames += 1
            face = runtime.face
            circle = runtime.circle
            rect = runtime.crop_rect

            # В прототипе tracker при потере лица круг не прыгает к центру.
            # Возврат оставлен только как осознанная настройка и включается
            # не мгновенно, чтобы не было дергания при одном-двух пропусках Haar.
            if circle is not None and runtime.lost_frames >= DYNAMIC_CROP_RETURN_AFTER_LOST_FRAMES:
                returned = self._dynamic_return_circle_to_frame_center(frame, circle)
                circle = self._dynamic_smooth_circle(circle, returned)
                rect = self._dynamic_crop_rect_from_circle(circle)
                runtime.stable_circle = returned
                runtime.circle = circle
                runtime.crop_rect = rect
            runtime.face_found = False

        self._ptz_process_dynamic_tracking(frame, runtime)

        if rect is None:
            return None

        crop = self._crop_rect_with_padding(frame, rect)
        if crop is None:
            return None

        if self.dynamic_crop.show_debug_view:
            crop = self._draw_dynamic_crop_debug(
                crop=crop,
                rect=rect,
                face=runtime.face,
                circle=circle,
                face_found=runtime.face_found,
            )
        return crop

    def _dynamic_adjust_offset(self, dx: float = 0.0, dy: float = 0.0):
        if not self.dynamic_crop.enabled:
            return
        max_offset = float(getattr(self.dynamic_crop, "max_composition_offset", MAX_COMPOSITION_OFFSET))
        if bool(getattr(self.dynamic_crop, "arrows_move_face", True)):
            self.dynamic_crop.offset_x = float(clamp(self.dynamic_crop.offset_x + dx, -max_offset, max_offset))
            self.dynamic_crop.offset_y = float(clamp(self.dynamic_crop.offset_y + dy, -max_offset, max_offset))
        else:
            self.dynamic_crop.circle_offset_x = float(clamp(getattr(self.dynamic_crop, "circle_offset_x", 0.0) + dx, -max_offset, max_offset))
            self.dynamic_crop.circle_offset_y = float(clamp(getattr(self.dynamic_crop, "circle_offset_y", 0.0) + dy, -max_offset, max_offset))
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._load_dynamic_from_owner()
                dlg._update_crop_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        if self.chroma.persist:
            self.save_config()

    def _dynamic_adjust_circle_to_head(self, delta: float) -> bool:
        if not self.dynamic_crop.enabled:
            return False
        self.dynamic_crop.circle_to_head = float(clamp(
            self.dynamic_crop.circle_to_head + delta,
            DYNAMIC_CROP_MIN_CIRCLE_TO_HEAD,
            DYNAMIC_CROP_MAX_CIRCLE_TO_HEAD,
        ))
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._load_dynamic_from_owner()
                dlg._update_crop_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        if self.chroma.persist:
            self.save_config()
        return True

    def _dynamic_adjust_analysis(self, delta: int):
        if not self.dynamic_crop.enabled:
            return
        self.dynamic_crop.analysis_scale_percent = int(clamp(
            self.dynamic_crop.analysis_scale_percent + int(delta),
            DYNAMIC_CROP_ANALYSIS_MIN,
            DYNAMIC_CROP_ANALYSIS_MAX,
        ))
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._load_dynamic_from_owner()
                dlg._update_crop_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        if self.chroma.persist:
            self.save_config()

    def _dynamic_toggle_debug_view(self) -> bool:
        if not self.dynamic_crop.enabled:
            return False
        self.set_dynamic_debug_view(not self.dynamic_crop.show_debug_view)
        return True

    def _dynamic_reset(self):
        if not self.dynamic_crop.enabled:
            return
        was_enabled = self.dynamic_crop.enabled
        self.dynamic_crop = DynamicCropConfig(enabled=was_enabled)
        self._dynamic_crop_runtime = DynamicCropRuntimeState()
        self._reset_face_director()
        self._sync_dynamic_menu_actions()
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._load_dynamic_from_owner()
                dlg._update_crop_label()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        if self.chroma.persist:
            self.save_config()

    # ------------------------------------------------------------------
    # Обработка кадров
    # ------------------------------------------------------------------
    def _on_tick(self):
        try:
            if getattr(self, "_shutdown_started", False):
                return
            if not (self.cap and self.cap.isOpened()):
                return
            if self._pending_frame_bgr is None or self._pending_frame_id == self._processed_frame_id:
                return
            frame = self._pending_frame_bgr
            self._processed_frame_id = self._pending_frame_id
            if frame is None:
                return
            if self._no_frame_count:
                _logger.info("Кадры восстановились после %d пропусков", self._no_frame_count)
                self._no_frame_count = 0

            self.last_frame_bgr = frame
            src = frame

            # Кроп для плавающего окна.
            # Динамический кроп имеет приоритет над ручным, но не меняет
            # self.crop.rect. Это временная автокомпозиция, а не новая
            # запись в ручной настройке.
            dynamic_src = None
            if self.dynamic_crop.enabled:
                dynamic_src = self._face_director_crop_source(frame)
                if dynamic_src is None:
                    dynamic_src = self._dynamic_crop_source(frame)
            if dynamic_src is not None:
                src = dynamic_src
            elif self.crop.enabled and self.crop.rect:
                x, y, w, h = self.crop.rect
                x2 = int(clamp(x, 0, src.shape[1] - 1))
                y2 = int(clamp(y, 0, src.shape[0] - 1))
                w2 = int(clamp(w, 1, src.shape[1] - x2))
                h2 = int(clamp(h, 1, src.shape[0] - y2))
                src = src[y2:y2+h2, x2:x2+w2].copy()

            # Кадр для виртуальной камеры — всегда полный кадр физической камеры.
            # Кроп относится только к плавающему окну и превью виньетки.
            # В режиме «как с физической камеры» это критично: в vcam не должно
            # попадать никаких пользовательских кропов, кеинга, виньеток и фонов.
            vcam_src = frame

            # Зеркало и масштаб для отображения в окне.
            # Важно: если dynamic crop вышел за границы физического кадра,
            # его технический чёрный padding уходит в отдельную alpha-маску.
            target = max(1, self.size().width())
            src_alpha = self._dynamic_crop_alpha_for_window(frame) if dynamic_src is not None else None
            roi, roi_source_alpha = self._fit_square_with_optional_alpha(
                src, target, alpha=src_alpha, mirror=bool(self.state.window_mirror))

            # Альфа-маска
            alpha = self._build_alpha(roi) if self.chroma.enabled else \
                    np.full((roi.shape[0], roi.shape[1]), 255, dtype=np.uint8)
            if roi_source_alpha is not None:
                alpha = (alpha.astype(np.uint16) * roi_source_alpha.astype(np.uint16) // 255).astype(np.uint8)

            if self.state.window_shape == "circle":
                size, should_shrink = self._window_visible_circle_size(roi)
                if should_shrink and size < min(roi.shape[:2]):
                    roi = self._shrink_into_canvas(roi, target, target,
                                                   scale=size / max(1, min(roi.shape[:2])))
                    if roi_source_alpha is not None:
                        roi_source_alpha = self._shrink_into_canvas(roi_source_alpha, target, target,
                                                                    scale=size / max(1, min(roi.shape[:2])),
                                                                    fill_value=0)
                        alpha = (alpha.astype(np.uint16) * roi_source_alpha.astype(np.uint16) // 255).astype(np.uint8)
                cm   = self._circle_mask(size)
                sm   = np.zeros((roi.shape[0], roi.shape[1]), dtype=np.uint8)
                oy = (roi.shape[0] - size) // 2
                ox = (roi.shape[1] - size) // 2
                sm[oy:oy+size, ox:ox+size] = cm
                alpha = (alpha.astype(np.uint16) * sm // 255).astype(np.uint8)

            rgb  = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            argb = np.dstack((rgb, alpha))
            qimg = QImage(argb.data, argb.shape[1], argb.shape[0], QImage.Format_RGBA8888)
            self._current_qpix = QPixmap.fromImage(qimg)
            self.update()

            # Виртуальная камера — независимый поток. Полный пайплайн
            # (масштаб, кеинг, фон, круг) собран в _compose_vcam_frame —
            # чтобы превью в диалоге могло использовать ровно ту же логику.
            if self.vcam is not None:
                out = self._compose_vcam_frame(vcam_src)
                if out is not None:
                    try:
                        self.vcam.send(out)
                        # В QTimer темп уже задаёт Qt. sleep_until_next_frame()
                        # блокирует GUI-поток и превращает живое окно в слайдшоу.
                    except Exception as e:
                        _log_exc("Ошибка отправки в vcam", e)
                        self._stop_vcam()
        except Exception as e:
            _log_exc("on_tick", e)

    def _build_alpha(self, bgr) -> np.ndarray:
        """Строит альфа-маску хромакея.

        Механика возвращена к v12:
          • если включён HSV — работает только HSV-диапазон;
          • если HSV выключен — работают только включённые пипетки;
          • пипетки и HSV не складываются через ИЛИ.

        Интерфейс 13-5 сохранён: 4 пипетки, h_wrap, отдельная мягкость
        кеинга, мягкость виньетки и масштаб основного окна.
        На выходе: uint8, где 255 = пиксель видим, 0 = пиксель скрыт.
        """
        if self.chroma.use_hsv:
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            h_min = int(clamp(self.chroma.h_min, 0, 179))
            h_max = int(clamp(self.chroma.h_max, 0, 179))
            s_min = int(clamp(self.chroma.s_min, 0, 255))
            s_max = int(clamp(self.chroma.s_max, 0, 255))
            v_min = int(clamp(self.chroma.v_min, 0, 255))
            v_max = int(clamp(self.chroma.v_max, 0, 255))

            if self.chroma.h_wrap and h_min > h_max:
                lo1 = np.array([h_min, s_min, v_min], dtype=np.uint8)
                hi1 = np.array([179,   s_max, v_max], dtype=np.uint8)
                lo2 = np.array([0,     s_min, v_min], dtype=np.uint8)
                hi2 = np.array([h_max, s_max, v_max], dtype=np.uint8)
                mask = cv2.bitwise_or(
                    cv2.inRange(hsv, lo1, hi1),
                    cv2.inRange(hsv, lo2, hi2)
                )
            else:
                lo = np.array([h_min, s_min, v_min], dtype=np.uint8)
                hi = np.array([h_max, s_max, v_max], dtype=np.uint8)
                mask = cv2.inRange(hsv, lo, hi)
        else:
            mask = np.zeros(bgr.shape[:2], dtype=np.uint8)
            bgr_f = None
            for slot in self.chroma.picks:
                if not slot.enabled or slot.color is None:
                    continue
                if bgr_f is None:
                    bgr_f = bgr.astype(np.float32)
                r, g, b = slot.color
                diff = bgr_f - np.array([b, g, r], dtype=np.float32)
                dist = np.sqrt((diff ** 2).sum(axis=2))
                mask = np.maximum(mask, (dist <= float(slot.tol)).astype(np.uint8) * 255)

        k = int(self.chroma.feather)
        if k > 0:
            k = k if k % 2 else k + 1
            mask = cv2.GaussianBlur(mask, (k, k), 0)

        return cv2.subtract(np.full_like(mask, 255), mask)

    def _circle_mask(self, size: int) -> np.ndarray:
        """Круглая маска виньетки, мягкий край построен аналитически
        через smoothstep(distance) — а не «бинарная маска + Gaussian Blur».

        Преимущества над v12/v14:
          • Симметрия идеальная: пиксель на нижнем краю, верхнем,
            левом и правом получает одинаковую α при одинаковом
            расстоянии от центра.
          • Радиус ровно size/2 — окно не «сжимается» при увеличении
            мягкости, как было в v14.
          • Не зависит от паддинга гаусса — нет проблемы «съедания»
            нижнего края у краёв буфера.

        edge_feather (0..100) интерпретируется как ширина зоны перехода
        в процентах от радиуса:
          • 0   → жёсткий чёрно-белый круг
          • 100 → переход от 1 к 0 занимает половину радиуса
        Результат кэшируется (один ключ — пересчёт только при смене
        size или edge_feather)."""
        f = max(0, int(self.state.edge_feather))
        key = (size, f)
        if key not in self._circle_mask_cache:
            self._circle_mask_cache.clear()   # держим только одну запись
            c = (size - 1) / 2.0
            radius = size / 2.0
            y, x = np.ogrid[:size, :size]
            dist = np.sqrt((x - c) ** 2 + (y - c) ** 2)

            if f == 0:
                # Жёсткий край (с антиалиасом в один пиксель).
                # Используем smoothstep шириной 1 пиксель — это уберёт
                # ступеньки на самом контуре, но визуально будет «резко».
                mask = np.clip(radius - dist + 0.5, 0.0, 1.0)
            else:
                # Ширина перехода: при f=100 — половина радиуса.
                # Минимум 2 пикселя, чтобы не было видимых ступенек.
                fw = max(2.0, radius * (f / 200.0))
                # Параметр t в [0, 1]: 0 на внешнем краю перехода,
                # 1 — на внутреннем. Центрируем переход на radius:
                # внутренний край перехода = radius - fw/2,
                # внешний край          = radius + fw/2.
                t = np.clip((radius + fw / 2.0 - dist) / fw, 0.0, 1.0)
                # Smoothstep — кубическая S-кривая, гладкие производные
                # на обоих концах. Выглядит мягче линейной градации.
                mask = t * t * (3.0 - 2.0 * t)

            self._circle_mask_cache[key] = (mask * 255.0).astype(np.uint8)
        return self._circle_mask_cache[key]

    # ------------------------------------------------------------------
    # Масштабирование и fit для виртуальной камеры
    # ------------------------------------------------------------------
    def _scale_circle(self, d: int):
        sz = int(clamp(self.state.circle_diameter + 20 * d, 120, 1080))
        self.state.circle_diameter = sz
        self.resize(sz, sz)

    def _center_crop(self, rgb, W, H) -> np.ndarray:
        h, w = rgb.shape[:2]
        scale = max(W / w, H / h)
        nw, nh = int(ceil(w * scale)), int(ceil(h * scale))
        rs = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        x, y = max(0, (nw-W)//2), max(0, (nh-H)//2)
        out = rs[y:y+H, x:x+W].copy()
        if out.shape[:2] != (H, W):
            pad = np.zeros((H, W, 3), dtype=out.dtype)
            pad[:out.shape[0], :out.shape[1]] = out; out = pad
        return out

    def _letterbox(self, rgb, W, H) -> np.ndarray:
        h, w = rgb.shape[:2]
        scale = min(W / w, H / h)
        nw, nh = int(w * scale), int(h * scale)
        rs  = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        out = np.zeros((H, W, 3), dtype=np.uint8)
        x, y = (W-nw)//2, (H-nh)//2
        out[y:y+nh, x:x+nw] = rs
        return out

    def _shrink_into_canvas(self, img: np.ndarray, out_w: int, out_h: int,
                            scale: float = 1.0, fill_value: int = 0) -> np.ndarray:
        """Уменьшает изображение и центрирует его в холсте фиксированного размера.

        Нужен для круглой виньетки: контент становится чуть меньше диаметра
        круга, благодаря чему мягкий край не упирается в границы окна/кадра,
        а в сам круг попадает чуть больше исходной сцены.
        """
        scale = float(clamp(scale, 0.05, 1.0))
        if img is None:
            return None
        if abs(scale - 1.0) < 1e-6 and img.shape[:2] == (out_h, out_w):
            return img
        target_w = max(1, int(round(out_w * scale)))
        target_h = max(1, int(round(out_h * scale)))
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        rs = cv2.resize(img, (target_w, target_h), interpolation=interp)
        if img.ndim == 3:
            out = np.full((out_h, out_w, img.shape[2]), fill_value, dtype=img.dtype)
        else:
            out = np.full((out_h, out_w), fill_value, dtype=img.dtype)
        ox, oy = (out_w - target_w) // 2, (out_h - target_h) // 2
        out[oy:oy + target_h, ox:ox + target_w] = rs
        return out

    # ------------------------------------------------------------------
    # Композиция кадра для виртуальной камеры
    # ------------------------------------------------------------------
    def _load_vcam_bg(self) -> np.ndarray | None:
        """Загружает (с кэшем) фон для виртуальной камеры.
        Возвращает BGR-картинку или None, если путь пуст/файла нет."""
        path = (self.state.vcam_bg_path or "").strip()
        if not path:
            return None
        if self._bg_cache.get("path") == path and self._bg_cache.get("img") is not None:
            return self._bg_cache["img"]
        if not os.path.exists(path):
            _logger.warning("vcam: фон не найден: %s", path)
            self._bg_cache = {"path": path, "img": None}
            return None
        try:
            # v13.3: cv2.imread не понимает Unicode-пути на Windows
            # (русские буквы → None). Читаем через np.fromfile + imdecode.
            data = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img is None:
                raise IOError("cv2.imdecode вернул None (не картинка?)")
        except Exception as e:
            _log_exc("vcam: ошибка загрузки фона", e)
            self._bg_cache = {"path": path, "img": None}
            return None
        self._bg_cache = {"path": path, "img": img}
        return img

    @staticmethod
    def detect_white_circle(bg_bgr: np.ndarray) -> tuple | None:
        """Ищет на фоне самый светлый круг (предположительно белый).
        Возвращает (x, y, r) в координатах bg_bgr — или None, если ничего
        не нашлось.

        Алгоритм:
          1. Конвертируем в grayscale.
          2. Слегка блюрим — Hough чувствителен к шуму.
          3. cv2.HoughCircles с диапазоном радиусов 5..50% от меньшей
             стороны (большинство «аватарных» кругов в этих границах).
          4. Из найденных кандидатов выбираем тот, у которого внутренняя
             область — самая светлая (это и есть «белый» круг).
        """
        if bg_bgr is None or bg_bgr.size == 0:
            return None
        h, w = bg_bgr.shape[:2]
        gray = cv2.cvtColor(bg_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        min_d = min(h, w)
        try:
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT,
                dp=1.2, minDist=min_d // 2,
                param1=100, param2=30,
                minRadius=int(min_d * 0.05),
                maxRadius=int(min_d * 0.50),
            )
        except Exception:
            return None
        if circles is None:
            return None
        circles = np.round(circles[0]).astype(int)
        # Выбираем самый «светлый» круг
        best = None; best_score = -1.0
        for (cx, cy, r) in circles:
            # Ограничим, чтобы не вылезать за края
            x0 = max(0, cx - r); y0 = max(0, cy - r)
            x1 = min(w, cx + r); y1 = min(h, cy + r)
            if x1 <= x0 or y1 <= y0:
                continue
            patch = gray[y0:y1, x0:x1]
            score = float(patch.mean())
            if score > best_score:
                best_score = score
                best = (int(cx), int(cy), int(r))
        # Минимальная яркость, чтобы считать «белым» — иначе мы вернём
        # любой круг даже на тёмном фоне. 180 — между «серым» и «белым».
        if best is None or best_score < 180:
            return None
        return best

    @staticmethod
    def _normalize_hex_color(value: str, default: str = "#202128") -> str:
        """Возвращает цвет в формате #RRGGBB. Некорректное значение заменяет default."""
        s = str(value or "").strip()
        if not s:
            s = default
        if not s.startswith("#"):
            s = "#" + s
        s = s.upper()
        if len(s) != 7:
            return default.upper()
        try:
            int(s[1:3], 16); int(s[3:5], 16); int(s[5:7], 16)
        except Exception:
            return default.upper()
        return s

    @classmethod
    def _hex_to_bgr(cls, value: str, default: str = "#202128") -> tuple[int, int, int]:
        color = cls._normalize_hex_color(value, default)
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return b, g, r

    def _apply_crop_for_window(self, frame: np.ndarray) -> np.ndarray:
        """Кроп только для плавающего окна и виньетки.

        Виртуальная камера в режиме «как с физической камеры» сюда не попадает.
        Режим «Телемост» использует эту функцию осознанно, потому что его
        второй слой — именно изображение виньетки, а не голый кадр камеры.
        Если включён динамический кроп, берём последний рассчитанный crop_rect
        из основного _on_tick(), не запускаем детектор повторно.
        """
        if frame is None:
            return frame

        if bool(getattr(self.dynamic_crop, "enabled", False)):
            runtime = getattr(self, "_dynamic_crop_runtime", None)
            rect = getattr(runtime, "crop_rect", None)
            if rect:
                crop = self._crop_rect_with_padding(frame, rect)
                if crop is not None:
                    return crop
            return frame

        if not (self.crop.enabled and self.crop.rect):
            return frame
        x, y, w, h = self.crop.rect
        fh, fw = frame.shape[:2]
        x = int(clamp(x, 0, max(0, fw - 1)))
        y = int(clamp(y, 0, max(0, fh - 1)))
        w = int(clamp(w, 1, max(1, fw - x)))
        h = int(clamp(h, 1, max(1, fh - y)))
        return frame[y:y + h, x:x + w].copy()

    def _compose_window_vignette_bgra(self, frame: np.ndarray, target_size: int, hard_edge: bool = False) -> tuple[np.ndarray, np.ndarray]:
        """Собирает ровно тот же визуальный слой, что и плавающее окно.

        Возвращает BGR и alpha одинакового размера target_size × target_size.
        Нужен для режима «Телемост», где виртуальная камера получает не
        отдельную новую композицию лица, а текущую виньетку КругоЗора как слой.
        """
        target = max(8, int(target_size))
        src = self._apply_crop_for_window(frame)
        src_alpha = self._dynamic_crop_alpha_for_window(frame) if bool(getattr(self.dynamic_crop, "enabled", False)) else None
        roi, roi_source_alpha = self._fit_square_with_optional_alpha(
            src, target, alpha=src_alpha, mirror=bool(self.state.window_mirror))

        if self.chroma.enabled:
            alpha = self._build_alpha(roi)
        else:
            alpha = np.full((target, target), 255, dtype=np.uint8)

        if roi_source_alpha is not None:
            alpha = (alpha.astype(np.uint16) * roi_source_alpha.astype(np.uint16) // 255).astype(np.uint8)

        if self.state.window_shape == "circle":
            visible_circle_size, should_shrink = self._window_visible_circle_size(roi)
            if should_shrink and visible_circle_size < min(roi.shape[:2]):
                scale = visible_circle_size / max(1, min(roi.shape[:2]))
                roi = self._shrink_into_canvas(roi, target, target, scale=scale)
                if roi_source_alpha is not None:
                    roi_source_alpha = self._shrink_into_canvas(roi_source_alpha, target, target,
                                                                scale=scale, fill_value=0)
                    alpha = (alpha.astype(np.uint16) * roi_source_alpha.astype(np.uint16) // 255).astype(np.uint8)

            cm = self._solid_circle_mask(visible_circle_size) if hard_edge else self._circle_mask(visible_circle_size)
            sm = np.zeros((target, target), dtype=np.uint8)
            oy = (target - visible_circle_size) // 2
            ox = (target - visible_circle_size) // 2
            sm[oy:oy + visible_circle_size, ox:ox + visible_circle_size] = cm
            alpha = (alpha.astype(np.uint16) * sm // 255).astype(np.uint8)

        return roi, alpha

    @staticmethod
    def _solid_circle_mask(size: int) -> np.ndarray:
        """Жёсткая круглая маска с антиалиасом только по самому контуру."""
        size = max(1, int(size))
        mask = np.zeros((size, size), dtype=np.uint8)
        center = (size // 2, size // 2)
        radius = max(1, size // 2)
        cv2.circle(mask, center, radius, 255, -1, lineType=cv2.LINE_AA)
        return mask

    @staticmethod
    def _place_mask(dst: np.ndarray, src: np.ndarray, x: int, y: int):
        """Кладёт одноканальную маску src в dst с обрезкой по границам."""
        H, W = dst.shape[:2]
        sh, sw = src.shape[:2]
        x0 = max(0, x); y0 = max(0, y)
        x1 = min(W, x + sw); y1 = min(H, y + sh)
        if x1 <= x0 or y1 <= y0:
            return
        sx0 = x0 - x; sy0 = y0 - y
        sx1 = sx0 + (x1 - x0); sy1 = sy0 + (y1 - y0)
        dst[y0:y1, x0:x1] = src[sy0:sy1, sx0:sx1]

    def _compose_telemost_layers(self, src_bgr: np.ndarray) -> np.ndarray | None:
        """Слойная сборка режима «Телемост».

        Порядок слоёв:
          1) нижняя подложка — белая или выбранный файл;
          2) изображение виньетки — то же, что в плавающем окне;
          3) фон аватарки с круглым вырезом.
        """
        W, H = self.vcam_w, self.vcam_h
        if W <= 0 or H <= 0:
            return None

        bg = self._load_vcam_bg()
        if bg is None:
            # Базовая пропорция Телемоста из старого пресета. Белая подложка
            # нужна не для красоты, а чтобы через прозрачные зоны кеинга не
            # лезла чёрная техническая пустота.
            bg = np.full((511, 855, 3), 255, dtype=np.uint8)

        bottom, off_x, off_y, sx, sy = self._fit_bg_to_vcam(bg)
        cx = int(self.state.vcam_circle_x * sx) + off_x
        cy = int(self.state.vcam_circle_y * sy) + off_y
        cr = int(self.state.vcam_circle_r * min(sx, sy))
        if cr < 4:
            cx, cy = W // 2, H // 2
            cr = max(4, min(W, H) // 4)

        # cr*2 — это диаметр ВНУТРЕННЕГО видимого круга аватарки.
        # Если dynamic crop добавил crop_padding, слой виньетки должен быть
        # больше, но его альфа-круг остаётся равен именно d, а не d*padding.
        d = max(8, cr * 2)
        inner_scale = self._dynamic_inner_circle_scale()
        if inner_scale is None:
            inner_scale = 1.0
        vignette_canvas = max(d, int(round(d / max(0.05, float(inner_scale)))))
        vignette_bgr, vignette_alpha = self._compose_window_vignette_bgra(
            src_bgr, vignette_canvas, hard_edge=True)

        out = bottom.copy()
        self._paste_with_alpha(out, vignette_bgr, vignette_alpha,
                               cx - vignette_canvas // 2,
                               cy - vignette_canvas // 2)

        avatar_bgr = self._hex_to_bgr(getattr(self.state, "vcam_avatar_bg_color", "#202128"))
        avatar_layer = np.full((H, W, 3), avatar_bgr, dtype=np.uint8)

        hole = self._solid_circle_mask(d)
        hole_full = np.zeros((H, W), dtype=np.uint8)
        self._place_mask(hole_full, hole, cx - cr, cy - cr)
        overlay_alpha = cv2.subtract(np.full((H, W), 255, dtype=np.uint8), hole_full)
        a = (overlay_alpha.astype(np.float32) / 255.0)[..., None]
        out = (avatar_layer.astype(np.float32) * a + out.astype(np.float32) * (1 - a)).astype(np.uint8)

        return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)

    def _compose_vcam_frame(self, src_bgr: np.ndarray) -> np.ndarray | None:
        """Собирает кадр для отправки в виртуальную камеру.

        Входной src_bgr должен быть полным кадром физической камеры.
        Пользовательский кроп сюда не передаётся: он применяется только
        к плавающему окну и превью виньетки.

        Этапы:
          1. Зеркало (если включено).
          2. Масштаб лица (scale 50..200%): ресайз исходника, затем
             центральный кроп/паддинг до vcam_w × vcam_h.
          3. Кеинг (если включён) — строится альфа-маска.
          4. Композиция в зависимости от vcam_mode:
             • passthrough — кадр с альфой как есть, прозрачные
                              области просто чёрные.
             • background  — фон (если загружен) подставляется под
                              прозрачные области.
             • circle      — режим «Телемост»: белая/выбранная подложка,
                              виньетка как в основном окне, верхний фон
                              аватарки с круглым вырезом.

        Возвращает RGB-кадр размером vcam_w × vcam_h.
        """
        if self.vcam_w <= 0 or self.vcam_h <= 0:
            return None

        # v13.3: режим «как с физической камеры» — ранний возврат.
        # Никакой обработки, отдаём оригинал в RGB. Размер vcam при
        # этом должен совпадать с размером src_bgr (за это отвечает
        # _start_vcam, который при passthrough_native берёт реальные
        # h/w из последнего кадра).
        if self.state.vcam_passthrough_native:
            f = cv2.flip(src_bgr, 1) if self.state.vcam_mirror else src_bgr
            # Если по какой-то причине размер не совпал — letterbox
            if f.shape[0] != self.vcam_h or f.shape[1] != self.vcam_w:
                f = self._letterbox(f, self.vcam_w, self.vcam_h)
            return cv2.cvtColor(f, cv2.COLOR_BGR2RGB)

        # Режим «Телемост» теперь не пытается заново собрать лицо через
        # отдельный кроп и Hough-круг. Он использует слои: нижняя подложка,
        # та же виньетка, что в окне, и верхняя плашка аватарки с вырезом.
        if self.state.vcam_mode == "circle":
            return self._compose_telemost_layers(src_bgr)

        # 1. Зеркало
        f = cv2.flip(src_bgr, 1) if self.state.vcam_mirror else src_bgr

        # 2. Масштаб + кадрирование до целевого размера vcam.
        scale_pct = clamp(self.state.vcam_scale, 50, 200)
        # Сначала вписываем исходник в целевой размер с сохранением пропорций
        # (letterbox) — это база. Если scale != 100, дополнительно изменяем.
        canvas = self._letterbox(f, self.vcam_w, self.vcam_h)
        if scale_pct != 100:
            k = scale_pct / 100.0
            nw, nh = int(self.vcam_w * k), int(self.vcam_h * k)
            if nw > 0 and nh > 0:
                resized = cv2.resize(canvas, (nw, nh), interpolation=cv2.INTER_AREA)
                if scale_pct > 100:
                    # «Зум» — берём центральный фрагмент целевого размера
                    cx = (nw - self.vcam_w) // 2
                    cy = (nh - self.vcam_h) // 2
                    canvas = resized[cy:cy + self.vcam_h,
                                     cx:cx + self.vcam_w].copy()
                else:
                    # «Уменьшение» — кладём в центр чёрного канваса
                    pad = np.zeros((self.vcam_h, self.vcam_w, 3), dtype=np.uint8)
                    px = (self.vcam_w - nw) // 2
                    py = (self.vcam_h - nh) // 2
                    pad[py:py + nh, px:px + nw] = resized
                    canvas = pad

        mode = self.state.vcam_mode
        circle_overlay_active = (self.state.vcam_circle_overlay and mode != "circle")

        # Если поверх vcam рисуется круглая виньетка, сначала немного
        # уменьшаем сам контент в кадре. Тогда в круг попадает чуть больше
        # сцены, а мягкий край не "съедает" полезную область.
        if circle_overlay_active:
            canvas = self._shrink_into_canvas(canvas, self.vcam_w, self.vcam_h,
                                              scale=VCAM_CIRCLE_CONTENT_SCALE)

        # 3. Альфа-маска кеинга (либо все 255 если кеинг выключен)
        if self.chroma.enabled:
            alpha = self._build_alpha(canvas)
        else:
            alpha = np.full((self.vcam_h, self.vcam_w), 255, dtype=np.uint8)

        # 3.5. Круглая виньетка поверх кеинга (опционально).
        # Применяется только в режимах passthrough/background — в режиме
        # circle лицо уже маскируется отдельной круглой маской по
        # детектированному кругу фона.
        if circle_overlay_active:
            vignette_scale = clamp(
                getattr(self.state, "vcam_vignette_scale", 100) / 100.0,
                0.50, 1.00)
            v_alpha = self._vcam_vignette_alpha(
                self.vcam_w, self.vcam_h, vignette_scale)
            alpha = (alpha.astype(np.uint16) * v_alpha // 255).astype(np.uint8)

        bg = self._load_vcam_bg() if mode in ("background", "circle") else None

        if mode == "circle" and bg is not None and self.state.vcam_circle_r > 0:
            # === Режим «лицо в круг» ===
            # 1) подгоняем фон под размер vcam (letterbox-копия)
            bg_fitted, off_x, off_y, sx, sy = self._fit_bg_to_vcam(bg)
            # 2) пересчитываем координаты круга из координат фона
            cx = int(self.state.vcam_circle_x * sx) + off_x
            cy = int(self.state.vcam_circle_y * sy) + off_y
            cr = int(self.state.vcam_circle_r * min(sx, sy))
            if cr < 4:
                # фон слишком мелкий относительно vcam — fallback на bg-режим
                return self._compose_with_background(canvas, alpha, bg_fitted)
            # 3) вырезаем «лицо» — берём центральный квадрат canvas размером 2r
            d = cr * 2
            face = self._center_square_crop(canvas, d)
            face_a = self._center_square_crop(alpha, d)
            # 4) маскируем face круглой маской
            cm = self._smoothstep_circle(d, max(2, d // 30))
            face_a = (face_a.astype(np.uint16) * cm // 255).astype(np.uint8)
            # 5) накладываем face на bg_fitted в позиции (cx, cy)
            out = bg_fitted.copy()
            self._paste_with_alpha(out, face, face_a,
                                    cx - cr, cy - cr)
            rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
            return rgb

        if mode == "background" and bg is not None:
            bg_fitted, *_ = self._fit_bg_to_vcam(bg)
            return self._compose_with_background(canvas, alpha, bg_fitted)

        # passthrough — прозрачные пиксели становятся чёрными.
        # Альфу применяем если включён кеинг ИЛИ круглая виньетка
        # (последнее даёт нетривиальную альфа-маску по эллипсу).
        if self.chroma.enabled or self.state.vcam_circle_overlay:
            a3 = (alpha.astype(np.float32) / 255.0)[..., None]
            canvas = (canvas.astype(np.float32) * a3).astype(np.uint8)
        return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

    def _compose_with_background(self, fg_bgr, alpha, bg_bgr) -> np.ndarray:
        """Стандартное альфа-смешивание fg на bg. Возвращает RGB."""
        a = alpha.astype(np.float32) / 255.0
        a3 = a[..., None]
        out = (fg_bgr.astype(np.float32) * a3
               + bg_bgr.astype(np.float32) * (1 - a3)).astype(np.uint8)
        return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)

    def _fit_bg_to_vcam(self, bg_bgr: np.ndarray):
        """Вписывает фон в размер vcam (letterbox). Возвращает кортеж:
        (fitted_bg, off_x, off_y, scale_x, scale_y) — чтобы можно было
        пересчитывать координаты круга из исходного фона в координаты
        получившегося кадра."""
        H, W = self.vcam_h, self.vcam_w
        h, w = bg_bgr.shape[:2]
        scale = min(W / w, H / h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        rs = cv2.resize(bg_bgr, (nw, nh), interpolation=cv2.INTER_AREA)
        # Заполняем оставшиеся поля цветом фона у краёв (чтобы не было
        # резкой чёрной рамки). Берём средний цвет рамки исходного фона.
        edge = np.concatenate([rs[0, :].reshape(-1, 3),
                               rs[-1, :].reshape(-1, 3),
                               rs[:, 0].reshape(-1, 3),
                               rs[:, -1].reshape(-1, 3)])
        fill_color = edge.mean(axis=0).astype(np.uint8)
        out = np.full((H, W, 3), fill_color, dtype=np.uint8)
        ox, oy = (W - nw) // 2, (H - nh) // 2
        out[oy:oy + nh, ox:ox + nw] = rs
        return out, ox, oy, scale, scale

    @staticmethod
    def _center_square_crop(img: np.ndarray, size: int) -> np.ndarray:
        """Берёт центральный квадрат size×size из img. Если img меньше —
        паддит чёрным."""
        h, w = img.shape[:2]
        out_shape = (size, size, 3) if img.ndim == 3 else (size, size)
        out = np.zeros(out_shape, dtype=img.dtype)
        sx = max(0, (w - size) // 2); sy = max(0, (h - size) // 2)
        cw = min(size, w - sx); ch = min(size, h - sy)
        ox = max(0, (size - w) // 2); oy = max(0, (size - h) // 2)
        out[oy:oy + ch, ox:ox + cw] = img[sy:sy + ch, sx:sx + cw]
        return out

    @staticmethod
    def _smoothstep_circle(size: int, feather_px: int) -> np.ndarray:
        """Аналитическая круглая маска с мягким краем (smoothstep).
        Используется для маскирования «лица в круг» — независимая от
        виньетки окна (та работает в координатах окна, эта — vcam)."""
        c = (size - 1) / 2.0
        radius = size / 2.0
        y, x = np.ogrid[:size, :size]
        dist = np.sqrt((x - c) ** 2 + (y - c) ** 2)
        fw = max(2.0, float(feather_px))
        t = np.clip((radius + fw / 2.0 - dist) / fw, 0.0, 1.0)
        return (t * t * (3.0 - 2.0 * t) * 255.0).astype(np.uint8)

    def _vcam_vignette_alpha(self, w: int, h: int, scale: float = 1.0) -> np.ndarray:
        """КРУГЛАЯ, а не овальная виньетка для виртуальной камеры.

        Раньше маска строилась как эллипс на весь прямоугольный кадр vcam,
        из-за чего круг в интерфейсе не совпадал с тем, что уходило наружу.
        Теперь строим именно круг диаметром min(w, h), дополнительно можно
        чуть уменьшить его через scale, чтобы оставить запас под мягкий край.
        """
        f = max(0, int(self.state.edge_feather))
        scale = float(clamp(scale, 0.05, 1.0))
        key = ("vcam_vig", w, h, f, round(scale, 4))
        cache = getattr(self, "_circle_mask_cache", {})
        if key in cache:
            return cache[key]

        d = max(1, int(round(min(w, h) * scale)))
        circle = self._circle_mask(d)
        mask = np.zeros((h, w), dtype=np.uint8)
        ox = max(0, (w - d) // 2)
        oy = max(0, (h - d) // 2)
        mask[oy:oy + d, ox:ox + d] = circle

        cache[key] = mask
        self._circle_mask_cache = cache
        return mask

    @staticmethod
    def _paste_with_alpha(dst_bgr, src_bgr, src_alpha, x: int, y: int):
        """Накладывает src_bgr с прозрачностью src_alpha на dst_bgr
        в позицию (x, y). Меняет dst_bgr in-place. Координаты могут
        быть отрицательными или выходить за границы — обрезается."""
        H, W = dst_bgr.shape[:2]
        sh, sw = src_bgr.shape[:2]
        # пересечение прямоугольников
        x0 = max(0, x); y0 = max(0, y)
        x1 = min(W, x + sw); y1 = min(H, y + sh)
        if x1 <= x0 or y1 <= y0:
            return
        sx0 = x0 - x; sy0 = y0 - y
        sx1 = sx0 + (x1 - x0); sy1 = sy0 + (y1 - y0)
        a = src_alpha[sy0:sy1, sx0:sx1].astype(np.float32) / 255.0
        a3 = a[..., None]
        sub = dst_bgr[y0:y1, x0:x1].astype(np.float32)
        sf  = src_bgr[sy0:sy1, sx0:sx1].astype(np.float32)
        dst_bgr[y0:y1, x0:x1] = (sf * a3 + sub * (1 - a3)).astype(np.uint8)

    # ------------------------------------------------------------------
    # Рендер и маска окна
    # ------------------------------------------------------------------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if hasattr(self, "_current_qpix"):
            p.drawPixmap(0, 0, self.width(), self.height(), self._current_qpix)

    def _update_mask(self):
        # Для квадрата — маски нет (окно прозрачное по умолчанию через
        # WA_TranslucentBackground). Для круга мы НЕ ставим жёсткий
        # QRegion.Ellipse: иначе он обрезает мягкий альфа-край виньетки
        # (особенно нижний), и сглаживание визуально пропадает.
        # Форма круга задаётся только альфа-маской в _on_tick.
        self.clearMask()

    def resizeEvent(self, ev):
        self._update_mask(); super().resizeEvent(ev)

    # ------------------------------------------------------------------
    # Мышь
    # ------------------------------------------------------------------
    def mousePressEvent(self, ev):
        if self.state.click_through: ev.ignore(); return
        if ev.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = ev.globalPos() - self.frameGeometry().topLeft()
            ev.accept()
        else:
            ev.ignore()

    def mouseMoveEvent(self, ev):
        if getattr(self, "_dragging", False) and not self.state.click_through:
            self.move(ev.globalPos() - self._drag_pos); ev.accept()
        else:
            ev.ignore()

    def mouseReleaseEvent(self, ev):
        if getattr(self, "_dragging", False):
            self._dragging = False
            g = self.geometry()
            self.state.pos_x, self.state.pos_y = g.left(), g.top()

    def contextMenuEvent(self, ev):
        if self.state.click_through:
            return
        self.ctx_menu.exec_(ev.globalPos())

    # ------------------------------------------------------------------
    # Вспомогательные диалоги
    # ------------------------------------------------------------------
    def get_last_frame(self):
        return self.last_frame_bgr

    def _open_crop_dialog(self):
        """Совместимость со старыми вызовами: отдельный попап кропа больше не открываем."""
        self._open_crop_settings()

    def _open_chroma_dialog(self, tab_index: int | None = None):
        """Открывает общее окно свойств.

        tab_index:
          0 — хромакей / виньетка;
          1 — кроп;
          2 — виртуальная камера;
          3 — PTZ.
        None оставляет текущую/первую вкладку как есть.
        """
        dlg = self._chroma_dlg
        if dlg is not None:
            try:
                if tab_index is not None and hasattr(dlg, "settings_tabs"):
                    dlg.settings_tabs.setCurrentIndex(int(clamp(tab_index, 0, dlg.settings_tabs.count() - 1)))
                if dlg.isVisible():
                    dlg.raise_(); dlg.activateWindow(); return
            except RuntimeError:
                # объект Qt уже удалён
                self._chroma_dlg = None
        dlg = ChromaDialog(self, self.chroma, self.get_last_frame, owner=self)
        dlg.setAttribute(Qt.WA_DeleteOnClose, True)
        dlg.destroyed.connect(self._on_chroma_dialog_destroyed)
        self._chroma_dlg = dlg
        if tab_index is not None and hasattr(dlg, "settings_tabs"):
            dlg.settings_tabs.setCurrentIndex(int(clamp(tab_index, 0, dlg.settings_tabs.count() - 1)))
        dlg.show(); dlg.raise_(); dlg.activateWindow()

    def _open_chroma_settings(self):
        self._open_chroma_dialog(0)

    def _open_crop_settings(self):
        self._open_chroma_dialog(1)

    def _open_vcam_settings(self):
        self._open_chroma_dialog(2)

    def _open_ptz_settings(self):
        self._open_chroma_dialog(3)

    def _on_chroma_dialog_destroyed(self, _obj=None):
        self._chroma_dlg = None

    def _open_hotkeys_dialog(self):
        """Открывает (или активирует) диалог редактирования шорткатов."""
        dlg = self._hotkeys_dlg
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_(); dlg.activateWindow(); return
            except RuntimeError:
                self._hotkeys_dlg = None
        dlg = HotkeysDialog(self, self.hotkeys, owner=self)
        dlg.setAttribute(Qt.WA_DeleteOnClose, True)
        dlg.destroyed.connect(lambda *_: setattr(self, "_hotkeys_dlg", None))
        self._hotkeys_dlg = dlg
        dlg.show(); dlg.raise_(); dlg.activateWindow()

    def _open_vcam_dialog(self):
        """Совместимость со старыми вызовами: отдельный попап виртуальной камеры больше не открываем."""
        self._open_vcam_settings()

    # ------------------------------------------------------------------
    # Горячие клавиши — динамическая привязка
    # ------------------------------------------------------------------
    def _dynamic_arrow_nudge(self, axis: str, direction: int):
        step = float(getattr(self.dynamic_crop, "nudge_step", COMPOSITION_NUDGE_STEP))
        if axis == "x":
            if bool(getattr(self.dynamic_crop, "invert_arrows_x", False)):
                direction = -direction
            self._dynamic_adjust_offset(float(direction) * step, 0.0)
        else:
            if bool(getattr(self.dynamic_crop, "invert_arrows_y", False)):
                direction = -direction
            self._dynamic_adjust_offset(0.0, float(direction) * step)

    def _hotkey_callback(self, hid: str):
        """Возвращает callable для действия hid. Используется внутри
        _apply_hotkeys, когда тип привязки 'shortcut' (без QAction)."""
        callbacks = {
            "vcam_toggle":   lambda: (self._dynamic_toggle_debug_view() or
                                       self.set_vcam_enabled(not self.state.vcam_enabled)),
            "vcam_mirror":   lambda: self.set_vcam_mirror(not self.state.vcam_mirror),
            "window_mirror": lambda: self.set_window_mirror(not self.state.window_mirror),
            "scale_up":      lambda: self._scale_circle(1),
            "scale_up_alt":  lambda: self._scale_circle(1),
            "scale_down":    lambda: self._scale_circle(-1),
            "dynamic_left":  lambda: self._dynamic_arrow_nudge("x", -1),
            "dynamic_right": lambda: self._dynamic_arrow_nudge("x", 1),
            "dynamic_up":    lambda: self._dynamic_arrow_nudge("y", -1),
            "dynamic_down":  lambda: self._dynamic_arrow_nudge("y", 1),
            "dynamic_analysis_down": lambda: self._dynamic_adjust_analysis(-DYNAMIC_CROP_ANALYSIS_STEP),
            "dynamic_analysis_up":   lambda: self._dynamic_adjust_analysis(DYNAMIC_CROP_ANALYSIS_STEP),
            "dynamic_analysis_down_alt": lambda: self._dynamic_adjust_analysis(-DYNAMIC_CROP_ANALYSIS_STEP),
            "dynamic_analysis_up_alt":   lambda: self._dynamic_adjust_analysis(DYNAMIC_CROP_ANALYSIS_STEP),
            "dynamic_reset": lambda: self._reset_camera_and_target_to_home(),
        }
        return callbacks.get(hid)

    def _apply_hotkeys(self):
        """Применяет текущий self.hotkeys к QAction-ам и QShortcut-ам.
        Безопасно вызывать многократно — старые QShortcut'ы сначала
        удаляются."""
        # Снести старые QShortcut'ы
        for sc in self._shortcuts:
            try: sc.setEnabled(False); sc.deleteLater()
            except Exception: pass
        self._shortcuts = []
        # Пройтись по реестру и применить новый seq
        for hid, _title, _default, kind, action_attr in HOTKEY_DEFINITIONS:
            seq_str = self.hotkeys.get(hid, "")
            if kind == "menu" and action_attr:
                act = getattr(self, action_attr, None)
                if act is None:
                    continue
                if seq_str:
                    act.setShortcut(QtGui.QKeySequence(seq_str))
                    act.setShortcutContext(Qt.ApplicationShortcut)
                else:
                    act.setShortcut(QtGui.QKeySequence())   # пусто
            elif kind == "shortcut":
                if not seq_str:
                    continue
                cb = self._hotkey_callback(hid)
                if cb is None:
                    continue
                sc = QShortcut(QtGui.QKeySequence(seq_str), self, activated=cb)
                sc.setContext(Qt.ApplicationShortcut)
                self._shortcuts.append(sc)

    # ------------------------------------------------------------------
    # Сброс настроек
    # ------------------------------------------------------------------
    def _safe_window_geometry(self):
        """Возвращает (x, y, size) для размещения окна на ОСНОВНОМ экране
        в безопасной зоне. Используется при сбросе позиции и при старте,
        если сохранённая позиция оказалась за пределами доступных экранов
        (например, отключили внешний монитор)."""
        size = 360
        try:
            screen = QApplication.primaryScreen()
            geo = screen.availableGeometry() if screen else QtCore.QRect(0, 0, 1280, 720)
        except Exception:
            geo = QtCore.QRect(0, 0, 1280, 720)
        # Чуть отступим от верхнего-левого угла основного экрана
        x = geo.left() + 100
        y = geo.top()  + 100
        # На всякий случай — окно должно гарантированно влезать
        size = min(size, max(120, min(geo.width(), geo.height()) - 200))
        return x, y, size

    def _is_position_visible(self, x: int, y: int, size: int) -> bool:
        """Проверяет, виден ли прямоугольник окна хотя бы частично
        на каком-нибудь подключённом экране."""
        try:
            rect = QtCore.QRect(x, y, size, size)
            for s in QApplication.screens():
                if s.availableGeometry().intersects(rect):
                    return True
            return False
        except Exception:
            return True   # в случае ошибки лучше не трогать позицию

    def reset_window_geometry(self):
        """Возвращает окно на главный экран в безопасные координаты.
        Полезно если внешний монитор был отключён и окно «улетело»."""
        x, y, size = self._safe_window_geometry()
        self.state.pos_x = x
        self.state.pos_y = y
        self.state.circle_diameter = size
        self.resize(size, size)
        self.move(x, y)
        if not self.isVisible():
            self.show(); self.raise_(); self.activateWindow()
        _logger.info("Сброс позиции окна: %d,%d size=%d", x, y, size)
        if self.chroma.persist:
            self.save_config()

    def reset_chroma(self):
        """Сбрасывает все параметры хромакея к дефолтным.
        Не трогает геометрию окна, кроп, общий feather виньетки."""
        keep_persist = self.chroma.persist
        keep_ui_op   = self.chroma.ui_opacity
        # Создаём свежий ChromaConfig — у него __post_init__ построит
        # дефолтные слоты PickSlot. Копируем поля по одному, чтобы
        # сохранить ИМЕННО тот же экземпляр self.chroma (на него
        # завязаны диалоги).
        defaults = ChromaConfig()
        for fname in ("enabled", "use_hsv", "h_min", "h_max", "s_min",
                      "s_max", "v_min", "v_max", "h_wrap", "feather",
                      "ui_opacity", "persist"):
            setattr(self.chroma, fname, getattr(defaults, fname))
        # picks — список PickSlot, копируем как новые объекты, чтобы
        # не делиться ссылками с defaults.
        self.chroma.picks = [
            PickSlot(enabled=s.enabled, color=s.color, tol=s.tol, pos=s.pos)
            for s in defaults.picks
        ]
        self.chroma.persist    = keep_persist
        self.chroma.ui_opacity = keep_ui_op
        self.set_chroma_enabled(False)
        # Если открыт диалог хромакея — обновим его поля
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._load_from_model()
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        _logger.info("Хромакей сброшен")
        self.update()
        if self.chroma.persist:
            self.save_config()

    def reset_all(self):
        """Сбрасывает ВСЕ настройки: state, chroma, crop, удаляет
        config.json. Требует подтверждения."""
        ans = QMessageBox.question(
            self, "Сбросить всё?",
            "Сбросить все настройки к значениям по умолчанию?\n\n"
            "Будут восстановлены: позиция и размер окна, форма, прозрачность, "
            "хромакей, кроп, динамический кроп. Файл config.json будет удалён.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        # Удаляем файл конфига (на случай, если persist выключен —
        # чтобы при следующем запуске точно были дефолты)
        try:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
        except Exception as e:
            _log_exc("Ошибка удаления config.json", e)

        # Применяем дефолты ко всем dataclass'ам — поля, не объекты.
        # Для ChromaConfig нужен особый случай: его picks — список
        # PickSlot, и asdict() ломает их в словари. Используем явный путь.
        for k, v in asdict(AppState()).items():
            setattr(self.state, k, v)
        for k, v in asdict(CropConfig()).items():
            setattr(self.crop, k, v)
        for k, v in asdict(DynamicCropConfig()).items():
            setattr(self.dynamic_crop, k, v)
        self._dynamic_crop_runtime = DynamicCropRuntimeState()
        self._reset_face_director()
        for k, v in asdict(PTZConfig()).items():
            setattr(self.ptz, k, v)
        self._ptz_runtime = PTZRuntimeState()
        # Хромакей — через тот же путь, что и reset_chroma
        defaults = ChromaConfig()
        for fname in ("enabled", "use_hsv", "h_min", "h_max", "s_min",
                      "s_max", "v_min", "v_max", "h_wrap", "feather",
                      "ui_opacity", "persist"):
            setattr(self.chroma, fname, getattr(defaults, fname))
        self.chroma.picks = [
            PickSlot(enabled=s.enabled, color=s.color, tol=s.tol, pos=s.pos)
            for s in defaults.picks
        ]

        # Применяем визуальные изменения
        self.setWindowOpacity(self.state.window_opacity)
        self._circle_mask_cache.clear()
        self.set_always_on_top(self.state.always_on_top)
        self.set_window_mirror(self.state.window_mirror)
        self.set_click_through(self.state.click_through)
        self.set_chroma_enabled(self.chroma.enabled)
        self.set_crop_mode(self._current_crop_mode(), save=False)
        self._set_window_shape(self.state.window_shape)
        self.act_vcam_fill.setChecked(self.state.vcam_fit == "fill")
        # Геометрия — на безопасное место
        self.reset_window_geometry()
        # Виртуальная камера возвращается к базовому профилю,
        # а не принудительно выключается.
        self.set_vcam_mirror(self.state.vcam_mirror)
        self.set_vcam_enabled(self.state.vcam_enabled)
        self.set_window_opacity_percent(int(self.state.window_opacity * 100))
        # Если открыт диалог хромакея — обновим
        dlg = getattr(self, "_chroma_dlg", None)
        if dlg is not None:
            try:
                dlg._load_from_model()
                dlg.vignette_sld.blockSignals(True)
                dlg.vignette_sld.setValue(self.state.edge_feather)
                dlg.vignette_sld.blockSignals(False)
            except (RuntimeError, AttributeError):
                self._chroma_dlg = None
        # Если открыт диалог виртуальной камеры — обновим его тоже
        vdlg = getattr(self, "_vcam_dlg", None)
        if vdlg is not None:
            try:
                vdlg._load_from_owner()
            except (RuntimeError, AttributeError):
                self._vcam_dlg = None
        _logger.info("Полный сброс настроек")
        if self.chroma.persist:
            self.save_config()
        QMessageBox.information(self, "Готово",
                                "Все настройки сброшены к значениям по умолчанию.")

    def _show_about(self):
        """Диалог «О программе» в стиле NumLockCalc:
        единое тёмное полотно с подзаголовками, без отдельных
        группбоксов; в шапке — иконка приложения и название/версия;
        в подвале — автор и канал.

        Шорткаты в этом окне НЕ показываются — для них есть отдельный
        диалог Hotkeys, который к тому же позволяет их редактировать.
        """
        dlg = QDialog(self)
        dlg.setWindowTitle(f"О программе — {APP_NAME}")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)
        dlg.setStyleSheet(STYLE_QSS)
        dlg.setMinimumWidth(440)

        # Шапка: иконка + название/версия (фон и иконку не трогаем)
        icon_lbl = QLabel()
        pix = self._icon.pixmap(64, 64)
        if not pix.isNull():
            icon_lbl.setPixmap(pix)
        icon_lbl.setFixedSize(72, 72)
        icon_lbl.setAlignment(Qt.AlignCenter)

        title_lbl = QLabel(
            f"<div style='font-size:18px;'><b>{APP_NAME}</b></div>"
            f"<div style='color:#aaa; margin-top:4px;'>Версия {APP_VERSION}</div>"
        )
        title_lbl.setTextFormat(Qt.RichText)

        head = QHBoxLayout()
        head.addWidget(icon_lbl)
        head.addSpacing(12)
        head.addWidget(title_lbl, 1)

        # Основной текст: единое HTML-полотно с подзаголовками <b>,
        # без отдельных QGroupBox-рамок (как в NumLockCalc).
        body_html = """
        <div style='color:#ddd; line-height:1.45;'>

        Круглое или квадратное окошко с камерой поверх всех окон.
        Полупрозрачное, с хромакеем и независимой виртуальной камерой
        для трансляций.<br><br>

        <b>Окно</b><br>
        Перетаскивается мышью; колёсиком или клавишами +/− меняется
        размер. Можно сделать прозрачным до невидимости и игнорирующим
        мышь — будет жить как индикатор поверх остальных окон.<br><br>

        <b>Кроп</b><br>
        Если камера выдаёт кадр с лишними полями, в диалоге «Кроп…»
        можно выделить рамку, и в окне будет показываться только она.
        Это же помогает «приблизить» лицо без потери качества.<br><br>

        <b>Хромакей</b><br>
        Удаление фона по цвету — до 4 пипеток одновременно плюс
        HSV-диапазон. Превью с переключателем «Оригинал / Результат /
        Маска» позволяет настроить кеинг прямо в диалоге, без слепого
        кручения ползунков.<br><br>

        <b>Виртуальная камера</b><br>
        Полностью обработанный поток (с кропом и зеркалом) отдаётся
        в систему как отдельная камера и доступен любым видеосвязям —
        Zoom, OBS, Discord. В отличие от окна, кадр виртуальной камеры
        не обрезается под форму окна и идёт в полном размере.<br><br>

        <b>Hotkeys</b><br>
        Все горячие клавиши настраиваются в отдельном окне «Hotkeys…».
        </div>
        """
        body = QLabel(body_html)
        body.setTextFormat(Qt.RichText)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextBrowserInteraction)

        # Подвал: автор и канал — компактно, как в NumLockCalc
        foot_html = (
            "<div style='color:#bbb;'>"
            "Автор: <b>Андрей Кудлай</b><br>"
            "Telegram автора: "
            "<a style='color:#7cf;' href='https://t.me/AKudlay_ru'>@AKudlay_ru</a><br>"
            "Канал проекта: "
            "<a style='color:#7cf;' href='https://t.me/RoundCam'>t.me/RoundCam</a>"
            "</div>"
        )
        foot = QLabel(foot_html)
        foot.setTextFormat(Qt.RichText)
        foot.setOpenExternalLinks(True)
        foot.setTextInteractionFlags(Qt.TextBrowserInteraction)
        foot.setStyleSheet("padding-top:8px;")

        ok_btn = QPushButton("Закрыть")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dlg.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(ok_btn)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(16, 14, 16, 12)
        lay.setSpacing(6)
        lay.addLayout(head)
        lay.addWidget(body)
        lay.addWidget(foot)
        lay.addStretch(1)
        lay.addLayout(btn_row)

        dlg.exec_()

    # ------------------------------------------------------------------
    # Конфиг
    # ------------------------------------------------------------------
    def _normalize_loaded_config(self) -> None:
        """Санитарная проверка config.json после мягкой загрузки.

        Файл настроек лежит рядом с программой и может быть повреждён,
        отредактирован руками или приехать из старой версии. Программа не
        должна из-за этого падать в рантайме. Да, JSON тоже иногда хочет
        участвовать в саботаже.
        """
        s = self.state
        defaults = AppState()

        s.camera_index = _clamp_int(s.camera_index, defaults.camera_index, 0, 32)
        if not isinstance(s.camera_aliases, dict):
            s.camera_aliases = {}
        else:
            s.camera_aliases = {str(k): str(v) for k, v in s.camera_aliases.items() if str(v).strip()}

        s.always_on_top = _as_bool(s.always_on_top, defaults.always_on_top)
        s.click_through = _as_bool(s.click_through, defaults.click_through)
        s.window_mirror = _as_bool(s.window_mirror, defaults.window_mirror)
        s.preview_mirror = _as_bool(getattr(s, "preview_mirror", defaults.preview_mirror), defaults.preview_mirror)
        s.vcam_enabled = _as_bool(s.vcam_enabled, defaults.vcam_enabled)
        s.vcam_mirror = _as_bool(s.vcam_mirror, defaults.vcam_mirror)
        s.vcam_circle_overlay = _as_bool(s.vcam_circle_overlay, defaults.vcam_circle_overlay)
        s.vcam_passthrough_native = _as_bool(s.vcam_passthrough_native, defaults.vcam_passthrough_native)

        s.circle_diameter = _clamp_int(s.circle_diameter, defaults.circle_diameter, 64, 4096)
        s.pos_x = _clamp_int(s.pos_x, defaults.pos_x, -20000, 20000)
        s.pos_y = _clamp_int(s.pos_y, defaults.pos_y, -20000, 20000)
        if s.window_shape not in ("circle", "square"):
            s.window_shape = defaults.window_shape
        s.window_opacity = _clamp_float(s.window_opacity, defaults.window_opacity, 0.05, 1.0)
        s.edge_feather = _clamp_int(s.edge_feather, defaults.edge_feather, 0, 200)
        s.window_content_scale = _clamp_int(s.window_content_scale, defaults.window_content_scale, 50, 150)
        s.vcam_vignette_scale = _clamp_int(s.vcam_vignette_scale, defaults.vcam_vignette_scale, 10, 120)
        s.vcam_scale = _clamp_int(s.vcam_scale, defaults.vcam_scale, 50, 200)
        if s.vcam_mode not in ("passthrough", "background", "circle"):
            s.vcam_mode = defaults.vcam_mode

        bg_path = str(getattr(s, "vcam_bg_path", "") or "").strip()
        if bg_path and not os.path.exists(bg_path):
            if _logger:
                _logger.warning("Сброшен невалидный путь подложки vcam: %s", bg_path)
            s.vcam_bg_path = ""
        else:
            s.vcam_bg_path = bg_path
        s.vcam_avatar_bg_color = _safe_hex_color(s.vcam_avatar_bg_color, defaults.vcam_avatar_bg_color)
        s.vcam_circle_x = _clamp_int(s.vcam_circle_x, defaults.vcam_circle_x, -10000, 10000)
        s.vcam_circle_y = _clamp_int(s.vcam_circle_y, defaults.vcam_circle_y, -10000, 10000)
        s.vcam_circle_r = _clamp_int(s.vcam_circle_r, defaults.vcam_circle_r, 1, 10000)
        s.vcam_circle_auto = _as_bool(s.vcam_circle_auto, defaults.vcam_circle_auto)

        c = self.chroma
        c.enabled = _as_bool(c.enabled, True)
        c.use_hsv = _as_bool(c.use_hsv, True)
        c.h_min = _clamp_int(c.h_min, 70, 0, 179)
        c.h_max = _clamp_int(c.h_max, 108, 0, 179)
        c.s_min = _clamp_int(c.s_min, 0, 0, 255)
        c.s_max = _clamp_int(c.s_max, 58, 0, 255)
        c.v_min = _clamp_int(c.v_min, 135, 0, 255)
        c.v_max = _clamp_int(c.v_max, 235, 0, 255)
        c.h_wrap = _as_bool(c.h_wrap, False)
        c.feather = _clamp_int(c.feather, 15, 0, 200)
        c.ui_opacity = _clamp_float(c.ui_opacity, 1.0, 0.25, 1.0)
        c.persist = _as_bool(c.persist, True)
        if not isinstance(c.picks, list):
            c.picks = ChromaConfig().picks
        normalized_picks = []
        for i in range(4):
            item = c.picks[i] if i < len(c.picks) else PickSlot(enabled=(i < 2))
            if isinstance(item, dict):
                item = PickSlot(**item)
            if not isinstance(item, PickSlot):
                item = PickSlot(enabled=(i < 2))
            item.enabled = _as_bool(item.enabled, i < 2)
            item.color = _safe_pick_color(item.color)
            item.tol = _clamp_int(item.tol, 30, 0, 255)
            item.pos = _safe_point(item.pos)
            normalized_picks.append(item)
        c.picks = normalized_picks

        self.crop.enabled = _as_bool(self.crop.enabled, True)
        self.crop.rect = _safe_rect(self.crop.rect, CropConfig().rect)

        d = self.dynamic_crop
        d.enabled = _as_bool(d.enabled, False)
        d.max_composition_offset = _clamp_float(d.max_composition_offset, 0.5, 0.05, 1.0)
        d.offset_x = _clamp_float(d.offset_x, 0.0, -d.max_composition_offset, d.max_composition_offset)
        d.offset_y = _clamp_float(d.offset_y, -0.05, -d.max_composition_offset, d.max_composition_offset)
        d.circle_offset_x = _clamp_float(d.circle_offset_x, 0.0, -d.max_composition_offset, d.max_composition_offset)
        d.circle_offset_y = _clamp_float(d.circle_offset_y, 0.0, -d.max_composition_offset, d.max_composition_offset)
        d.circle_to_head = _clamp_float(d.circle_to_head, 2.0, 1.0, 4.0)
        d.crop_padding = _clamp_float(d.crop_padding, 1.08, 1.0, 2.5)
        d.analysis_scale_percent = _clamp_int(d.analysis_scale_percent, 25, 25, 100)
        d.smoothing = _clamp_float(d.smoothing, DEFAULT_SMOOTHING, 0.03, 0.85)
        d.position_smoothing = _clamp_float(getattr(d, "position_smoothing", d.smoothing), d.smoothing, 0.03, 0.85)
        d.scale_smoothing = _clamp_float(getattr(d, "scale_smoothing", 0.22), 0.22, 0.03, 0.85)
        d.position_dead_zone = _clamp_float(getattr(d, "position_dead_zone", getattr(d, "center_dead_zone", 0.06)), 0.06, 0.0, 0.5)
        d.scale_dead_zone = _clamp_float(getattr(d, "scale_dead_zone", 0.08), 0.08, 0.0, 0.5)
        # Старые поля синхронизируем, чтобы fallback-логика не жила своей жизнью.
        d.smoothing = d.position_smoothing
        d.center_dead_zone = d.position_dead_zone
        d.tracking_mode = str(getattr(d, "tracking_mode", "eyes_ipd") or "eyes_ipd").lower()
        if d.tracking_mode not in ("eyes_ipd", "face_box"):
            d.tracking_mode = "eyes_ipd"
        d.fast_roi_tracking = _as_bool(d.fast_roi_tracking, True)
        d.face_roi_margin = _clamp_float(d.face_roi_margin, 2.8, 1.0, 8.0)
        d.detector_min_neighbors = _clamp_int(d.detector_min_neighbors, 4, 2, 12)
        d.return_speed = _clamp_float(d.return_speed, 0.0, 0.0, 1.0)
        d.center_dead_zone = _clamp_float(d.center_dead_zone, 0.12, 0.0, 0.5)
        d.min_face_size_full_frame = _clamp_int(d.min_face_size_full_frame, 80, 20, 1000)
        d.vignette_panel_width = _clamp_int(d.vignette_panel_width, 360, 120, 1200)
        d.nudge_step = _clamp_float(d.nudge_step, 0.01, 0.001, 0.2)
        d.arrows_move_face = _as_bool(d.arrows_move_face, True)
        d.invert_arrows_x = _as_bool(d.invert_arrows_x, False)
        d.invert_arrows_y = _as_bool(d.invert_arrows_y, False)
        d.show_debug_view = _as_bool(d.show_debug_view, False)
        d.detector = str(getattr(d, "detector", "mediapipe") or "mediapipe").lower()
        if d.detector not in ("mediapipe", "haar", "opencv", "cv2"):
            d.detector = "mediapipe"

        p = self.ptz
        p.enabled = _as_bool(p.enabled, False)
        p.trigger_edge_guard = _as_bool(p.trigger_edge_guard, True)
        p.trigger_focus_vertical_thirds = _as_bool(p.trigger_focus_vertical_thirds, True)
        p.edge_guard_percent = _clamp_int(p.edge_guard_percent, 10, 1, 40)
        p.focus_third_percent = _clamp_int(p.focus_third_percent, 33, 5, 49)
        p.cooldown_frames = _clamp_int(p.cooldown_frames, 8, 1, 120)
        p.pan_step = _clamp_float(p.pan_step, 8.0, 0.1, 1000.0)
        p.tilt_step = _clamp_float(p.tilt_step, 8.0, 0.1, 1000.0)
        p.zoom_step = _clamp_float(p.zoom_step, 4.0, 0.1, 1000.0)
        p.pan_min = _clamp_float(p.pan_min, -100.0, -10000.0, 9999.0)
        p.pan_max = _clamp_float(p.pan_max, 100.0, p.pan_min + 1.0, 10000.0)
        p.tilt_min = _clamp_float(p.tilt_min, -100.0, -10000.0, 9999.0)
        p.tilt_max = _clamp_float(p.tilt_max, 100.0, p.tilt_min + 1.0, 10000.0)
        p.zoom_min = _clamp_float(p.zoom_min, 0.0, -10000.0, 9999.0)
        p.zoom_max = _clamp_float(p.zoom_max, 200.0, p.zoom_min + 1.0, 10000.0)
        p.invert_pan = _as_bool(p.invert_pan, False)
        p.invert_tilt = _as_bool(p.invert_tilt, False)
        p.invert_zoom = _as_bool(p.invert_zoom, False)
        p.show_debug = _as_bool(p.show_debug, False)
        for attr in ("home_pan", "home_tilt", "home_zoom"):
            value = getattr(p, attr)
            if value is not None:
                setattr(p, attr, _clamp_float(value, 0.0, -10000.0, 10000.0))
        p.home_offset_x = _clamp_float(p.home_offset_x, 0.0, -d.max_composition_offset, d.max_composition_offset)
        p.home_offset_y = _clamp_float(p.home_offset_y, -0.05, -d.max_composition_offset, d.max_composition_offset)
        p.home_circle_offset_x = _clamp_float(p.home_circle_offset_x, 0.0, -d.max_composition_offset, d.max_composition_offset)
        p.home_circle_offset_y = _clamp_float(p.home_circle_offset_y, 0.0, -d.max_composition_offset, d.max_composition_offset)

        if hasattr(self, "hotkeys") and isinstance(self.hotkeys, dict):
            clean = dict(DEFAULT_HOTKEYS)
            for hid in clean:
                if hid in self.hotkeys:
                    clean[hid] = str(self.hotkeys[hid])
            self.hotkeys = clean

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("config.json должен содержать JSON-объект")

            # --- Миграция со старой схемы хромакея (v14 и раньше) ---
            # Если в config.json лежат поля pickA/pickB/tolA/tolB и нет
            # нового списка picks — собираем picks из старых полей.
            cs = data.get("chroma", {})
            if not isinstance(cs, dict):
                cs = {}
                data["chroma"] = cs
            if "picks" not in cs and any(k in cs for k in
                                          ("pickA", "pickB", "tolA", "tolB")):
                picks = [
                    {"enabled": cs.get("pickA") is not None,
                     "color":   cs.get("pickA"),
                     "tol":     cs.get("tolA", 30),
                     "pos":     None},
                    {"enabled": cs.get("pickB") is not None,
                     "color":   cs.get("pickB"),
                     "tol":     cs.get("tolB", 30),
                     "pos":     None},
                    {"enabled": False, "color": None, "tol": 30, "pos": None},
                    {"enabled": False, "color": None, "tol": 30, "pos": None},
                ]
                # Если оба слота были None — оставим A и B включёнными по
                # умолчанию (как в свежем ChromaConfig), но без цвета.
                if not picks[0]["enabled"] and not picks[1]["enabled"]:
                    picks[0]["enabled"] = True
                    picks[1]["enabled"] = True
                cs["picks"] = picks
                # Старые ключи больше не нужны
                for k in ("pickA", "pickB", "tolA", "tolB"):
                    cs.pop(k, None)
                _logger.info("Хромакей: мигрирована старая схема pickA/B → picks[]")

            for section, obj in (("state", self.state),
                                  ("chroma", self.chroma),
                                  ("crop",   self.crop),
                                  ("dynamic_crop", self.dynamic_crop),
                                  ("ptz", self.ptz)):
                if section in data:
                    sect = data[section]
                    if not isinstance(sect, dict):
                        if _logger:
                            _logger.warning("Секция config.json %s проигнорирована: ожидался объект", section)
                        continue
                    # Особый случай: picks у chroma — это список словарей,
                    # их нужно восстановить как PickSlot.
                    if section == "chroma" and "picks" in sect:
                        raw = sect["picks"]
                        if not isinstance(raw, list):
                            raw = []
                        slots = []
                        for i in range(4):
                            if i < len(raw) and isinstance(raw[i], dict):
                                slots.append(PickSlot(**{
                                    "enabled": raw[i].get("enabled", i < 2),
                                    "color":   raw[i].get("color"),
                                    "tol":     raw[i].get("tol", 30),
                                    "pos":     raw[i].get("pos"),
                                }))
                            else:
                                slots.append(PickSlot(enabled=(i < 2)))
                        obj.picks = slots
                        sect = {k: v for k, v in sect.items() if k != "picks"}
                    for k, v in sect.items():
                        if hasattr(obj, k):
                            setattr(obj, k, v)
            # v9: старый дефолт smoothing=0.20 давал заметное отставание.
            # Если в config приехало именно старое дефолтное значение, поднимаем
            # его до живого режима. Пользовательские экстремальные значения не трогаем.
            try:
                if 0.18 <= float(getattr(self.dynamic_crop, "smoothing", DEFAULT_SMOOTHING)) <= 0.22:
                    self.dynamic_crop.smoothing = DEFAULT_SMOOTHING
            except Exception:
                pass

            # v_face_director_2: старые дефолты автокомпозиции давали почти
            # тот же визуальный результат, что прежний динамический кроп.
            # Мигрируем только типовые старые значения, пользовательские настройки не трогаем.
            try:
                dc = self.dynamic_crop
                if 1.95 <= float(getattr(dc, "circle_to_head", 2.0)) <= 2.05:
                    dc.circle_to_head = 1.55
                if 1.06 <= float(getattr(dc, "crop_padding", 1.08)) <= 1.10:
                    dc.crop_padding = 1.02
                if 0.10 <= float(getattr(dc, "center_dead_zone", 0.12)) <= 0.14:
                    dc.center_dead_zone = 0.06
                if -0.07 <= float(getattr(dc, "offset_y", -0.05)) <= -0.03:
                    dc.offset_y = -0.14
            except Exception:
                pass

            # v4 face-director: разделяем позицию и масштаб. Если config.json
            # приехал из старой схемы, позицию берём из smoothing/center_dead_zone,
            # а масштаб делаем спокойнее, чтобы он не дышал от площади лица.
            try:
                raw_dynamic = data.get("dynamic_crop", {}) if isinstance(data, dict) else {}
                if not isinstance(raw_dynamic, dict):
                    raw_dynamic = {}
                dc = self.dynamic_crop
                if "position_smoothing" not in raw_dynamic:
                    dc.position_smoothing = float(getattr(dc, "smoothing", DEFAULT_SMOOTHING))
                if "position_dead_zone" not in raw_dynamic:
                    dc.position_dead_zone = float(getattr(dc, "center_dead_zone", DEFAULT_DYNAMIC_CENTER_DEAD_ZONE))
                if "scale_smoothing" not in raw_dynamic:
                    dc.scale_smoothing = 0.22
                if "scale_dead_zone" not in raw_dynamic:
                    dc.scale_dead_zone = 0.08
                if "tracking_mode" not in raw_dynamic:
                    dc.tracking_mode = "eyes_ipd"
            except Exception:
                pass

            # v10: старые шаги PTZ=1.0 почти незаметны на части камер.
            # Если в config приехали именно прежние дефолты, поднимаем до
            # рабочих значений. Пользовательские настройки выше 1.0 не трогаем.
            try:
                if 0.9 <= float(getattr(self.ptz, "pan_step", 8.0)) <= 1.1:
                    self.ptz.pan_step = 8.0
                if 0.9 <= float(getattr(self.ptz, "tilt_step", 8.0)) <= 1.1:
                    self.ptz.tilt_step = 8.0
                if 0.9 <= float(getattr(self.ptz, "zoom_step", 4.0)) <= 1.1:
                    self.ptz.zoom_step = 4.0
            except Exception:
                pass

            self._normalize_loaded_config()

            # --- Hotkeys ---
            if "hotkeys" in data and isinstance(data["hotkeys"], dict):
                # Берём только известные id; чужие ключи игнорируем.
                # Для ненайденных id — оставляем дефолт.
                self.hotkeys = dict(DEFAULT_HOTKEYS)
                for hid in self.hotkeys:
                    if hid in data["hotkeys"]:
                        self.hotkeys[hid] = str(data["hotkeys"][hid])
            self._normalize_loaded_config()
            _logger.info("Конфиг загружен")
        except Exception as e:
            _log_exc("Ошибка загрузки конфига", e)

    def _config_payload(self) -> dict:
        self._normalize_loaded_config()
        return {
            "state": asdict(self.state),
            "chroma": asdict(self.chroma),
            "crop": asdict(self.crop),
            "dynamic_crop": asdict(self.dynamic_crop),
            "ptz": asdict(self.ptz),
            "hotkeys": dict(getattr(self, "hotkeys", DEFAULT_HOTKEYS)),
        }

    def save_config(self, immediate: bool = False):
        """Сохраняет config.json.

        По умолчанию сохранение отложено на 250 мс: это гасит лавину записей
        при перетаскивании ползунков. При выходе вызывается immediate=True.
        """
        if immediate or not hasattr(self, "_save_timer"):
            self._save_config_now()
            return
        try:
            self._save_timer.start(250)
        except Exception:
            self._save_config_now()

    def _save_config_now(self):
        try:
            payload = self._config_payload()
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                dir=os.path.dirname(CONFIG_FILE),
                prefix="config.",
                suffix=".json",
                text=True,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except OSError:
                        pass
                os.replace(tmp_name, CONFIG_FILE)
            finally:
                if os.path.exists(tmp_name):
                    try:
                        os.remove(tmp_name)
                    except OSError:
                        pass
        except Exception as e:
            _log_exc("Ошибка сохранения конфига", e)

    # ------------------------------------------------------------------
    # Завершение / скрытие окна
    # ------------------------------------------------------------------
    def _cleanup_resources(self):
        """Идемпотентная очистка ресурсов при полном выходе."""
        if getattr(self, "_shutdown_done", False):
            return
        self._shutdown_started = True
        self._shutdown_done = True

        try:
            if self.chroma.persist:
                self.save_config(immediate=True)
        except Exception as e:
            _log_exc("Ошибка сохранения конфига при выходе", e)

        for attr in ("_chroma_dlg", "_hotkeys_dlg", "_vcam_dlg"):
            try:
                dlg = getattr(self, attr, None)
                if dlg is not None:
                    dlg.blockSignals(True)
                    dlg.close()
                    dlg.deleteLater()
                    setattr(self, attr, None)
            except Exception:
                pass

        try:
            if getattr(self, "_save_timer", None) is not None:
                self._save_timer.stop()
        except Exception:
            pass

        try:
            if getattr(self, "_frame_timer", None) is not None:
                self._frame_timer.stop()
                try:
                    self._frame_timer.timeout.disconnect(self._on_tick)
                except Exception:
                    pass
        except Exception:
            pass

        self._stop_vcam()

        self._stop_capture_loop(release=True, log=True)

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

        try:
            if getattr(self, "tray", None) is not None:
                self.tray.hide()
                self.tray.setContextMenu(None)
                self.tray.deleteLater()
        except Exception:
            pass

        _logger.info("Завершение: ресурсы освобождены")

    def force_quit(self):
        """Полный выход из программы: vcam и физическая камера закрываются."""
        if getattr(self, "_shutdown_started", False):
            app = QApplication.instance()
            if app is not None:
                QtCore.QTimer.singleShot(0, app.quit)
            return
        self._cleanup_resources()
        self.hide()
        app = QApplication.instance()
        if app is not None:
            QtCore.QTimer.singleShot(0, app.quit)

    def closeEvent(self, ev: QCloseEvent):
        """Закрытие окна не равно выходу: окно скрывается в трей.

        Полный выход выполняется только через пункт меню «Выход» / Ctrl+Q
        или при завершении QApplication. Это позволяет оставить
        виртуальную камеру включённой без плавающего окна на экране.
        """
        if getattr(self, "_shutdown_started", False):
            ev.accept()
            return
        ev.ignore()
        try:
            self.tray_act_show.blockSignals(True)
            self.tray_act_show.setChecked(False)
            self.tray_act_show.blockSignals(False)
        except Exception:
            pass
        self._on_tray_show(False)

# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------
def _parse_size(s: str):
    try:
        a, b = s.lower().split("x")
        w, h = int(a), int(b)
        if w <= 0 or h <= 0 or w > 7680 or h > 4320:
            raise ValueError
        return w, h
    except Exception:
        raise argparse.ArgumentTypeError("Ожидается формат WxH, напр. 1920x1080, значения > 0")

def _cli_int_range(name: str, lo: int, hi: int):
    def parse(raw: str) -> int:
        try:
            value = int(raw)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name}: нужно целое число")
        if value < lo or value > hi:
            raise argparse.ArgumentTypeError(f"{name}: допустимо {lo}..{hi}")
        return value
    return parse

def main():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} – камера в круге/квадрате")
    parser.add_argument("--camera",      type=_cli_int_range("camera", 0, 32), default=None)
    parser.add_argument("--fps",         type=_cli_int_range("fps", 1, 120), default=30)
    parser.add_argument("--width",       type=_cli_int_range("width", 0, 7680), default=0)
    parser.add_argument("--height",      type=_cli_int_range("height", 0, 4320), default=0)
    # --vcam-res — необязательный override. Если не задан, vcam подстроится
    # под фактическое разрешение физической камеры (одинаковые пропорции →
    # никаких чёрных полос/обрезаний).
    parser.add_argument("--vcam_res",    "--vcam-res",
                        type=_parse_size, default=None,
                        dest="vcam_res")
    parser.add_argument("--start-hidden",action="store_true")
    parser.add_argument("--debug",       action="store_true")
    args = parser.parse_args()
    if (args.width == 0) != (args.height == 0):
        parser.error("--width и --height нужно задавать вместе либо не задавать вовсе")
    # Сохраним «было ли указано» в отдельный атрибут — нужен в RoundCamWindow
    args.vcam_res_explicit = args.vcam_res

    try: ctypes.windll.kernel32.FreeConsole()
    except Exception: pass

    if not _ensure_single_instance():
        sys.exit(0)

    setup_logger(debug=args.debug)
    _logger.info("CLI: %s", vars(args))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    # Единый стиль на всё приложение — меню, диалоги, кнопки.
    # Источник: STYLE_QSS (либо встроенный, либо из style.qss рядом со скриптом).
    app.setStyleSheet(STYLE_QSS)
    _logger.info("Папка данных: %s", DATA_DIR)
    _logger.info("Файл стиля:   %s%s", STYLE_FILE,
                 " (есть)" if os.path.exists(STYLE_FILE) else " (нет)")

    w = RoundCamWindow(args)
    app.aboutToQuit.connect(w._cleanup_resources)
    if args.start_hidden:
        w.tray_act_show.setChecked(False)
    else:
        w.tray_act_show.setChecked(True)
        w.show(); w.raise_(); w.activateWindow()

    exit_code = app.exec_()
    w._cleanup_resources()
    _release_instance_mutex()
    sys.exit(exit_code)

# ---------------------------------------------------------------------------
# Встроенная иконка (base64 .ico) — генерируется один раз
# ---------------------------------------------------------------------------
_ICON_B64 = (
    "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"
    "/w9gHY5MYqjvsgAAAABJRU5ErkJggg=="
)

if __name__ == "__main__":
    main()
