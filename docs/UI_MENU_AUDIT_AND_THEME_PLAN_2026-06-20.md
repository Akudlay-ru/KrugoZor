# UI menu audit and theme plan — 2026-06-20

## Context

Current video result is verified as ideal. Production work must preserve the video pipeline and focus on interface clarity.

Current code builds shared actions for context menu and tray menu, then fills both menus through one `_fill_menu()` method. This is good: UX cleanup can be done in one place.

## Current menu tree

### Tray-only header

```text
Показать окно
---
Камера: —
Кроп: —
PTZ: —
VCam: —
---
```

Decision:
- keep status lines in tray only;
- rename `VCam` to `Вирт. камера` for Russian UI consistency;
- add status color/icon later: Off / Starting / Live / Error.

### Shared context/tray menu

```text
Выключить камеру

Окно
  Всегда поверх
  Отразить зеркально
  Прокликиваемый
  ---
  Круг
  Квадрат
  ---
  Увеличить окно
  Уменьшить окно
  ---
  <camera list>
  Обновить список камер

Хромакей / виньетка
  Хромакей: вкл/выкл
  Настройки хромакея / виньетки…

Кроп
  Выключен
  Включен
  Динамический
  ---
  Автозум
  Зафиксировать масштаб сейчас
  Показывать разметку динамического кропа
  ---
  Настройки кропа…

Виртуальная камера
  Вкл/выкл
  Отразить зеркально
  Виртуальная камера…

PTZ / цель
  Цель композиции
    ← Цель
    Цель →
    ↑ Цель
    Цель ↓
    ---
    Зафиксировать масштаб сейчас
  Физическая камера
    Pan ←
    Pan →
    Tilt ↑
    Tilt ↓
    ---
    Zoom +
    Zoom −
  ---
  Авто-PTZ Pan/Tilt
  Запомнить базовое положение камеры и цели
  Вернуть камеру и цель к базе
  ---
  Настройки PTZ…

Свойства…

Сброс
  Позиция и размер окна
  Сбросить хромакей
  Сбросить всё…

Hotkeys…
О программе…
---
Выход
```

## Problems

| Area | Problem | Decision |
|---|---|---|
| Top action | `Выключить камеру` is isolated and ambiguous | Rename to `Камера: выключить` / `Камера: включить`; keep at top |
| Window menu | Camera list lives under `Окно` | Move cameras to separate `Камера` submenu |
| `Прокликиваемый` | Technical word | Rename to `Игнорировать мышь` with tooltip |
| `Хромакей / виньетка` | Contains mixed concepts | Rename to `Фон и край` or split in settings only |
| `Кроп` | User does not know manual vs dynamic | Rename to `Кадрирование`; show modes as `Без кадрирования`, `Ручной кроп`, `Авто лицо` |
| `Показывать разметку...` | Debug item in normal menu | Move to Advanced/Diagnostics |
| PTZ | Too technical and disabled in known-good preset | Move under `Дополнительно` / `Экспериментально` |
| `Hotkeys…` | Mixed language | Rename to `Горячие клавиши…` |
| `VCam` | Mixed language in tray status | Rename to `Вирт. камера` |
| `Свойства…` | Not descriptive enough | Rename to `Все настройки…` |
| Reset | Dangerous items too close to normal actions | Keep, but move `Сбросить всё…` to bottom with confirmation |

## Target menu tree for production candidate

```text
Камера: выключить / Камера: включить

Режим
  Простая камера
  Хромакей
  Авто лицо

Камера
  <camera list with alias + resolution/FPS>
  Обновить список камер
  Переименовать текущую камеру…

Окно
  Всегда поверх
  Игнорировать мышь
  Отразить зеркально
  ---
  Форма
    Круг
    Квадрат
  Размер
    Увеличить
    Уменьшить
    Сбросить размер и позицию

Фон и край
  Хромакей включён
  Настроить фон…
  Настроить мягкий край…

Кадрирование
  Без кадрирования
  Ручной кроп
  Авто лицо
  ---
  Автозум
  Зафиксировать масштаб
  Пресет
    Стабильный портрет
    Быстрое слежение
    Ручная доводка
  Настроить кадрирование…

Виртуальная камера
  Включить / Выключить
  Отразить зеркально
  Режим вывода
    Круг в кадре
    Letterbox
    Простая подложка
  Настроить виртуальную камеру…

Интерфейс
  Тема
    Как в системе
    Светлая
    Тёмная
    Тёмная Win11
  Плотность
    Обычная
    Компактная
  Показывать подсказки

Дополнительно
  PTZ / физическая камера
    Включить авто-PTZ
    Цель композиции
      Влево
      Вправо
      Вверх
      Вниз
    Физическая камера
      Pan left
      Pan right
      Tilt up
      Tilt down
      Zoom in
      Zoom out
    Запомнить базу
    Вернуться к базе
    Настройки PTZ…
  Диагностика
    Показать разметку авто лица
    Открыть лог
    Скопировать диагностику

Все настройки…
Горячие клавиши…
О программе…

Сброс
  Сбросить хромакей
  Сбросить кадрирование
  Сбросить настройки интерфейса
  Сбросить всё…

Выход
```

## Settings window target structure

```text
Все настройки
  Быстрый старт
    1. Камера
    2. Фон / хромакей
    3. Авто лицо
    4. Виртуальная камера
  Камера
  Фон и край
  Кадрирование
  Виртуальная камера
  Интерфейс
    Тема: Как в системе / Светлая / Тёмная / Тёмная Win11
    Плотность: обычная / компактная
    Подсказки: включить / выключить
  Горячие клавиши
  Дополнительно
    PTZ
    Диагностика
```

## Theme implementation plan

Use the CalcNumLock approach:

- `interface_theme`: `system`, `light`, `dark`, optionally `dark_win11`;
- `normalize_theme_mode()`;
- `active_palette()`;
- `apply_theme_mode()`;
- rebuild `STYLE_QSS` or switch loaded QSS by theme;
- save theme in `config.json` under `state.interface_theme` or top-level `ui.interface_theme`.

Minimum implementation:

1. Add `interface_theme` to config model.
2. Add menu `Интерфейс > Тема` with radio actions.
3. Add settings tab `Интерфейс` with the same radio choices.
4. Reapply QApplication stylesheet when theme changes.
5. Update native Windows titlebar if possible.
6. Keep `style.qss` as fallback/default external file.

## Action order

1. Do not change video pipeline.
2. Rename confusing menu items.
3. Move cameras out of `Окно` into `Камера`.
4. Move PTZ/debug into `Дополнительно`.
5. Add `Интерфейс > Тема`.
6. Add preset menu for dynamic crop.
7. Add first-run setup later, after menu cleanup.
