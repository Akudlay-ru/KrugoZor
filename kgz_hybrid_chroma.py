"""Маска человека MediaPipe и её сочетание с цветовым хромакеем."""
from pathlib import Path

import cv2
import numpy as np


def soften_person_confidence(confidence: np.ndarray, feather: int) -> np.ndarray:
    """Смягчает границу наружу, не уменьшая исходную маску человека."""
    mask = np.clip(np.nan_to_num(confidence.astype(np.float32), nan=0.0), 0.0, 1.0)
    size = max(0, min(201, int(feather)))
    if size <= 0:
        return mask
    size = size if size % 2 else size + 1
    expanded_size = max(1, min(9, (size // 5) | 1))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (expanded_size, expanded_size))
    expanded = cv2.dilate(mask, kernel)
    softened = cv2.GaussianBlur(expanded, (size, size), 0)
    return np.maximum(mask, softened)


def sample_dynamic_pick(frame: np.ndarray, pos, previous, confidence, *, rate=0.35):
    """Считывает медианный цвет фона и не обучается на человеке."""
    if frame is None or confidence is None or confidence.shape != frame.shape[:2]:
        return previous
    try:
        x, y = int(pos[0]), int(pos[1])
    except (TypeError, ValueError, IndexError):
        return previous
    height, width = frame.shape[:2]
    if not (0 <= x < width and 0 <= y < height):
        return previous
    x0, x1 = max(0, x - 2), min(width, x + 3)
    y0, y1 = max(0, y - 2), min(height, y + 3)
    guard = confidence[y0:y1, x0:x1]
    if not np.isfinite(guard).all() or float(np.max(guard)) >= 0.35:
        return previous
    bgr = np.median(frame[y0:y1, x0:x1].reshape(-1, 3), axis=0)
    rgb = (float(bgr[2]), float(bgr[1]), float(bgr[0]))
    if previous is None:
        return rgb
    rate = max(0.0, min(1.0, float(rate)))
    return tuple(float(old) + rate * (new - float(old)) for old, new in zip(previous, rgb))


def combine_hybrid_alpha(color_alpha: np.ndarray, confidence: np.ndarray) -> np.ndarray:
    """Сохраняет человека и уточняет неопределённые пиксели цветовой маской."""
    if confidence.shape != color_alpha.shape:
        raise ValueError("Размеры масок не совпадают")
    person = np.nan_to_num(confidence.astype(np.float32), nan=0.0, posinf=1.0, neginf=0.0)
    person = cv2.min(cv2.max(person, 0.0), 1.0)
    uncertain = cv2.multiply(person, cv2.subtract(1.0, person))
    detail = cv2.multiply(uncertain, color_alpha.astype(np.float32), scale=1.0 / 255.0)
    return cv2.convertScaleAbs(cv2.add(person, detail), alpha=255.0)


class HybridSegmenter:
    def __init__(self, model_path: Path):
        import mediapipe as mp
        self._mp = mp
        options = mp.tasks.vision.ImageSegmenterOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            output_confidence_masks=True,
        )
        self._segmenter = mp.tasks.vision.ImageSegmenter.create_from_options(options)

    def confidence(self, bgr: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._segmenter.segment(image)
        if not result.confidence_masks:
            raise RuntimeError("Модель не вернула маску человека")
        mask = result.confidence_masks[-1].numpy_view().copy()
        if mask.ndim == 3 and mask.shape[2] == 1:
            mask = mask[:, :, 0]
        if mask.shape != bgr.shape[:2]:
            mask = cv2.resize(mask, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
        return mask

    def close(self):
        self._segmenter.close()
