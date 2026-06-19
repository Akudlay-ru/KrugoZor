# -*- coding: utf-8 -*-
"""Face auto-director for KruGoZor v4.

Камеру, Qt и virtual cam не трогает. Модуль получает BGR-кадр,
возвращает crop + metadata. MediaPipe/landmarks используются опционально.
Если mediapipe не установлен или не дал пригодные глаза/IPD, модуль
мягко откатывается на размер лица через Haar/рамку.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Optional

import cv2
import numpy as np


@dataclass
class FaceDirectorConfig:
    enabled: bool = False
    detector: str = "mediapipe"
    tracking_mode: str = "eyes_ipd"  # eyes_ipd | face_box
    analysis_scale_percent: int = 50
    min_face_size_full_frame: int = 80

    # Backward-compatible field; if split fields are absent, it works as position smoothing.
    smoothing: float = 0.42
    position_smoothing: float = 0.42
    scale_smoothing: float = 0.22

    # Backward-compatible field; if split fields are absent, it works as position dead zone.
    center_dead_zone: float = 0.06
    position_dead_zone: float = 0.06
    scale_dead_zone: float = 0.08

    circle_to_head: float = 1.55
    crop_padding: float = 1.20
    offset_x: float = 0.0
    offset_y: float = -0.07
    circle_offset_x: float = 0.0
    circle_offset_y: float = -0.07
    return_speed: float = 0.0
    show_debug_view: bool = False
    fast_roi_tracking: bool = True
    face_roi_margin: float = 2.8
    detector_min_neighbors: int = 4
    return_after_lost_frames: int = 18

    # Preview / UX build: scale control is explicit now.
    # auto  : current behaviour, diameter follows detected face/IPD size.
    # locked: face position is tracked, but crop diameter stays fixed.
    # manual: diameter is a user-controlled ratio of the shorter frame side.
    auto_zoom_enabled: bool = False
    zoom_mode: str = "locked"  # auto | locked | manual
    locked_diameter_ratio: Optional[float] = None
    manual_diameter_ratio: float = 0.42
    auto_zoom_min_ratio: float = 0.18
    auto_zoom_max_ratio: float = 0.80

    # Rough anthropometric projection: head/face width from interpupillary distance.
    # It is not medical geometry, just a stable video-composition estimate.
    ipd_to_head: float = 2.65


@dataclass
class FaceBox:
    x: float
    y: float
    w: float
    h: float
    anchor_x: Optional[float] = None
    anchor_y: Optional[float] = None
    scale_size: Optional[float] = None
    scale_source: str = "face"
    ipd: Optional[float] = None

    @property
    def cx(self) -> float:
        return float(self.anchor_x) if self.anchor_x is not None else self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return float(self.anchor_y) if self.anchor_y is not None else self.y + self.h / 2.0

    @property
    def box_size(self) -> float:
        return max(float(self.w), float(self.h))

    @property
    def size(self) -> float:
        return float(self.scale_size) if self.scale_size is not None and self.scale_size > 1 else self.box_size


@dataclass
class CircleState:
    cx: float
    cy: float
    diameter: float


@dataclass
class FaceDirectorResult:
    face_found: bool = False
    face: Optional[FaceBox] = None
    raw_face: Optional[FaceBox] = None
    circle: Optional[CircleState] = None
    target_circle: Optional[CircleState] = None
    stable_circle: Optional[CircleState] = None
    crop_rect: Optional[list[int]] = None
    crop_bgr: Optional[np.ndarray] = None
    crop_alpha: Optional[np.ndarray] = None
    debug_bgr: Optional[np.ndarray] = None
    lost_frames: int = 0
    processed_frames: int = 0
    detector_backend: str = "none"
    landmarks: Optional[list[tuple[float, float]]] = None
    scale_source: str = "none"
    zoom_mode: str = "locked"
    auto_zoom_enabled: bool = False


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


class FaceAutoDirector:
    """Stateful face crop/virtual director."""

    def __init__(self) -> None:
        self._haar_detector = None
        self._haar_failed = False
        self._mp = None
        self._mp_face_mesh = None
        self._mediapipe_failed = False
        self._last_backend = "none"
        self._last_landmarks: list[tuple[float, float]] = []
        self._last_scale_source = "none"
        self.reset()

    def reset(self) -> None:
        self.raw_face: Optional[FaceBox] = None
        self.previous_face: Optional[FaceBox] = None
        self.face: Optional[FaceBox] = None
        self.circle: Optional[CircleState] = None
        self.target_circle: Optional[CircleState] = None
        self.stable_circle: Optional[CircleState] = None
        self.crop_rect: Optional[list[int]] = None
        self.face_found = False
        self.lost_frames = 0
        self.processed_frames = 0
        self._last_backend = "none"
        self._last_landmarks = []
        self._last_scale_source = "none"

    def close(self) -> None:
        mesh = self._mp_face_mesh
        self._mp_face_mesh = None
        if mesh is not None:
            try:
                mesh.close()
            except Exception:
                pass

    def process(self, frame_bgr: np.ndarray, cfg: FaceDirectorConfig) -> FaceDirectorResult:
        self.processed_frames += 1
        if frame_bgr is None or frame_bgr.size == 0 or not bool(cfg.enabled):
            self.face_found = False
            self._last_scale_source = "disabled" if cfg is not None and not bool(getattr(cfg, "enabled", False)) else "none"
            return self._empty_result(cfg)

        detected_face = self._detect_face(frame_bgr, cfg)

        if detected_face is not None:
            self.raw_face = detected_face
            self.previous_face = detected_face
            self.lost_frames = 0

            self.face = self._smooth_box(self.face, detected_face, cfg)
            self.target_circle = self._circle_from_face(self.face, cfg, frame_bgr.shape)
            self.stable_circle = self._apply_dead_zones(self.circle, self.target_circle, self.face, cfg)
            self.circle = self._smooth_circle(self.circle, self.stable_circle, cfg)
            self.crop_rect = self._crop_rect_from_circle(self.circle, cfg)
            self.face_found = True
            self._last_scale_source = self.face.scale_source
        else:
            self.lost_frames += 1
            self.face_found = False
            if self.circle is not None and self.lost_frames >= int(_clamp(cfg.return_after_lost_frames, 1, 120)):
                returned = self._return_circle_to_frame_center(frame_bgr, self.circle, cfg)
                self.stable_circle = returned
                self.circle = self._smooth_circle(self.circle, returned, cfg)
                self.crop_rect = self._crop_rect_from_circle(self.circle, cfg)

        return self._result(frame_bgr, cfg)

    def _result(self, frame_bgr: Optional[np.ndarray], cfg: Optional[FaceDirectorConfig]) -> FaceDirectorResult:
        crop = None
        crop_alpha = None
        debug = None
        if frame_bgr is not None and self.crop_rect is not None:
            crop, crop_alpha = self._crop_rect_with_padding(frame_bgr, self.crop_rect, return_alpha=True)
            if crop is not None and cfg is not None and bool(cfg.show_debug_view):
                debug = self._draw_debug(crop, cfg)
        return FaceDirectorResult(
            face_found=bool(self.face_found),
            face=self._copy_face(self.face),
            raw_face=self._copy_face(self.raw_face),
            circle=self._copy_circle(self.circle),
            target_circle=self._copy_circle(self.target_circle),
            stable_circle=self._copy_circle(self.stable_circle),
            crop_rect=list(self.crop_rect) if self.crop_rect is not None else None,
            crop_bgr=crop,
            crop_alpha=crop_alpha,
            debug_bgr=debug,
            lost_frames=int(self.lost_frames),
            processed_frames=int(self.processed_frames),
            detector_backend=str(self._last_backend),
            landmarks=list(self._last_landmarks) if self._last_landmarks else None,
            scale_source=str(self._last_scale_source),
            zoom_mode=self._zoom_mode(cfg) if cfg is not None else "locked",
            auto_zoom_enabled=bool(getattr(cfg, "auto_zoom_enabled", False)) if cfg is not None else False,
        )

    def _empty_result(self, cfg: Optional[FaceDirectorConfig]) -> FaceDirectorResult:
        return FaceDirectorResult(
            face_found=False,
            lost_frames=int(self.lost_frames),
            processed_frames=int(self.processed_frames),
            detector_backend=str(self._last_backend),
            scale_source=str(self._last_scale_source),
            zoom_mode=self._zoom_mode(cfg) if cfg is not None else "locked",
            auto_zoom_enabled=bool(getattr(cfg, "auto_zoom_enabled", False)) if cfg is not None else False,
        )

    @staticmethod
    def _copy_face(face: Optional[FaceBox]) -> Optional[FaceBox]:
        if face is None:
            return None
        return FaceBox(
            float(face.x), float(face.y), float(face.w), float(face.h),
            None if face.anchor_x is None else float(face.anchor_x),
            None if face.anchor_y is None else float(face.anchor_y),
            None if face.scale_size is None else float(face.scale_size),
            str(face.scale_source),
            None if face.ipd is None else float(face.ipd),
        )

    @staticmethod
    def _copy_circle(circle: Optional[CircleState]) -> Optional[CircleState]:
        if circle is None:
            return None
        return CircleState(float(circle.cx), float(circle.cy), float(circle.diameter))

    @staticmethod
    def _mode(cfg: FaceDirectorConfig) -> str:
        mode = str(getattr(cfg, "tracking_mode", "eyes_ipd") or "eyes_ipd").lower()
        return mode if mode in ("eyes_ipd", "face_box") else "eyes_ipd"

    @staticmethod
    def _pos_alpha(cfg: FaceDirectorConfig) -> float:
        return float(_clamp(float(getattr(cfg, "position_smoothing", getattr(cfg, "smoothing", 0.42))), 0.03, 0.85))

    @staticmethod
    def _scale_alpha(cfg: FaceDirectorConfig) -> float:
        return float(_clamp(float(getattr(cfg, "scale_smoothing", 0.22)), 0.03, 0.85))

    @staticmethod
    def _pos_dead(cfg: FaceDirectorConfig) -> float:
        return float(_clamp(float(getattr(cfg, "position_dead_zone", getattr(cfg, "center_dead_zone", 0.06))), 0.0, 0.50))

    @staticmethod
    def _scale_dead(cfg: FaceDirectorConfig) -> float:
        return float(_clamp(float(getattr(cfg, "scale_dead_zone", 0.08)), 0.0, 0.50))

    @staticmethod
    def _zoom_mode(cfg: Optional[FaceDirectorConfig]) -> str:
        if cfg is None:
            return "locked"
        raw = str(getattr(cfg, "zoom_mode", "locked") or "locked").lower()
        if bool(getattr(cfg, "auto_zoom_enabled", False)):
            raw = "auto"
        if raw not in ("auto", "locked", "manual"):
            raw = "auto" if bool(getattr(cfg, "auto_zoom_enabled", False)) else "locked"
        return raw

    def _diameter_from_face(self, face: FaceBox, cfg: FaceDirectorConfig, frame_shape) -> float:
        h, w = frame_shape[:2]
        ref = max(1.0, float(min(w, h)))
        mode = self._zoom_mode(cfg)

        if mode == "manual":
            ratio = _clamp(float(getattr(cfg, "manual_diameter_ratio", 0.42)), 0.05, 2.0)
            return max(40.0, ref * ratio)

        raw = max(40.0, float(face.size) * float(cfg.circle_to_head))

        if mode == "locked":
            ratio = getattr(cfg, "locked_diameter_ratio", None)
            try:
                ratio = None if ratio is None else float(ratio)
            except Exception:
                ratio = None
            if ratio is not None and np.isfinite(ratio) and ratio > 0:
                return max(40.0, ref * _clamp(ratio, 0.05, 2.0))
            if self.circle is not None:
                return max(40.0, float(self.circle.diameter))
            return raw

        lo = ref * _clamp(float(getattr(cfg, "auto_zoom_min_ratio", 0.18)), 0.02, 1.5)
        hi = ref * _clamp(float(getattr(cfg, "auto_zoom_max_ratio", 0.80)), 0.05, 2.5)
        if hi < lo:
            lo, hi = hi, lo
        return float(_clamp(raw, lo, hi))

    def _ensure_mediapipe(self):
        if self._mediapipe_failed:
            return None
        if self._mp_face_mesh is not None:
            return self._mp_face_mesh
        try:
            import mediapipe as mp  # type: ignore
            self._mp = mp
            self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.50,
                min_tracking_confidence=0.50,
            )
            return self._mp_face_mesh
        except Exception:
            self._mediapipe_failed = True
            self._mp_face_mesh = None
            return None

    def _ensure_haar_detector(self):
        if self._haar_failed:
            return None
        if self._haar_detector is not None:
            return self._haar_detector
        try:
            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            detector = cv2.CascadeClassifier(path)
            if detector.empty():
                self._haar_failed = True
                return None
            self._haar_detector = detector
            return detector
        except Exception:
            self._haar_failed = True
            return None

    def _detect_face(self, frame_bgr: np.ndarray, cfg: FaceDirectorConfig) -> Optional[FaceBox]:
        detector_name = str(getattr(cfg, "detector", "mediapipe") or "mediapipe").lower()
        self._last_landmarks = []

        if detector_name in ("mediapipe", "mp", "landmarks"):
            found = self._detect_face_mediapipe(frame_bgr, cfg)
            if found is not None:
                self._last_backend = "mediapipe"
                return found
            found = self._detect_face_haar(frame_bgr, cfg)
            if found is not None:
                self._last_backend = "haar-fallback"
            else:
                self._last_backend = "none"
            return found

        found = self._detect_face_haar(frame_bgr, cfg)
        self._last_backend = "haar" if found is not None else "none"
        return found

    def _detect_face_mediapipe(self, frame_bgr: np.ndarray, cfg: FaceDirectorConfig) -> Optional[FaceBox]:
        mesh = self._ensure_mediapipe()
        if mesh is None:
            return None

        h, w = frame_bgr.shape[:2]
        scale_percent = _clamp(float(cfg.analysis_scale_percent), 25.0, 100.0)
        scale_factor = scale_percent / 100.0
        if scale_factor < 0.999:
            small = cv2.resize(frame_bgr, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
        else:
            small = frame_bgr
        if small is None or small.size == 0:
            return None

        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        try:
            result = mesh.process(rgb)
        except Exception:
            return None

        faces = getattr(result, "multi_face_landmarks", None)
        if not faces:
            return None

        face_landmarks = faces[0].landmark
        sh, sw = small.shape[:2]
        pts = []
        for lm in face_landmarks:
            x = float(lm.x) * sw / scale_factor
            y = float(lm.y) * sh / scale_factor
            if -w <= x <= 2 * w and -h <= y <= 2 * h:
                pts.append((x, y))
        if not pts:
            return None

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x1, x2 = max(0.0, min(xs)), min(float(w), max(xs))
        y1, y2 = max(0.0, min(ys)), min(float(h), max(ys))
        bw = max(1.0, x2 - x1)
        bh = max(1.0, y2 - y1)
        if max(bw, bh) < max(20, int(cfg.min_face_size_full_frame) * 0.55):
            return None

        mode = self._mode(cfg)

        # FaceMesh landmarks. Усреднение по нескольким точкам устойчивее,
        # чем одна точка века, особенно при моргании и шуме.
        left_eye_indices = [33, 133, 159, 145, 160, 144]
        right_eye_indices = [362, 263, 386, 374, 385, 373]

        def center_of(indices):
            acc = []
            for idx in indices:
                if 0 <= idx < len(face_landmarks):
                    lm = face_landmarks[idx]
                    acc.append((float(lm.x) * sw / scale_factor,
                                float(lm.y) * sh / scale_factor))
            if not acc:
                return None
            return (sum(p[0] for p in acc) / len(acc),
                    sum(p[1] for p in acc) / len(acc))

        left_eye = center_of(left_eye_indices)
        right_eye = center_of(right_eye_indices)

        ipd = None
        eye_anchor = None
        if left_eye is not None and right_eye is not None:
            ipd = hypot(left_eye[0] - right_eye[0], left_eye[1] - right_eye[1])
            if 8.0 <= ipd <= max(16.0, float(w) * 0.65):
                eye_anchor = ((left_eye[0] + right_eye[0]) / 2.0,
                              (left_eye[1] + right_eye[1]) / 2.0)
            else:
                ipd = None

        if mode == "eyes_ipd" and eye_anchor is not None:
            anchor_x, anchor_y = eye_anchor
            if ipd is not None:
                scale_size = float(ipd) * float(getattr(cfg, "ipd_to_head", 2.65))
                scale_source = "ipd"
            else:
                scale_size = max(bw, bh)
                scale_source = "face-fallback"
        else:
            anchor_x = x1 + bw / 2.0
            anchor_y = y1 + bh / 2.0
            scale_size = max(bw, bh)
            scale_source = "face"

        self._last_landmarks = pts[::max(1, len(pts) // 64)]
        return FaceBox(
            x1, y1, bw, bh,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            scale_size=scale_size,
            scale_source=scale_source,
            ipd=ipd,
        )

    def _detect_face_haar(self, frame_bgr: np.ndarray, cfg: FaceDirectorConfig) -> Optional[FaceBox]:
        detector = self._ensure_haar_detector()
        if detector is None:
            return None

        h, w = frame_bgr.shape[:2]
        scale_percent = _clamp(float(cfg.analysis_scale_percent), 10.0, 100.0)
        scale_factor = scale_percent / 100.0
        min_neighbors = int(_clamp(int(cfg.detector_min_neighbors), 3, 8))
        min_face_full = max(24, int(cfg.min_face_size_full_frame))
        previous = self.previous_face or self.raw_face or self.face

        def detect_in_region(region: np.ndarray, x0: int, y0: int, previous_full: Optional[FaceBox]) -> Optional[FaceBox]:
            if region is None or region.size == 0:
                return None
            if scale_factor < 0.999:
                small = cv2.resize(region, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
            else:
                small = region
            if small is None or small.size == 0:
                return None
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
                previous_small = FaceBox(
                    (previous_full.x - x0) * scale_factor,
                    (previous_full.y - y0) * scale_factor,
                    previous_full.w * scale_factor,
                    previous_full.h * scale_factor,
                    None if previous_full.anchor_x is None else (previous_full.anchor_x - x0) * scale_factor,
                    None if previous_full.anchor_y is None else (previous_full.anchor_y - y0) * scale_factor,
                    None if previous_full.scale_size is None else previous_full.scale_size * scale_factor,
                    previous_full.scale_source,
                    None if previous_full.ipd is None else previous_full.ipd * scale_factor,
                )
            detected_small = self._choose_best_face(faces, previous_small)
            if detected_small is None:
                return None
            x = x0 + detected_small.x / scale_factor
            y = y0 + detected_small.y / scale_factor
            bw = detected_small.w / scale_factor
            bh = detected_small.h / scale_factor
            return FaceBox(
                x, y, bw, bh,
                anchor_x=x + bw / 2.0,
                anchor_y=y + bh / 2.0,
                scale_size=max(bw, bh),
                scale_source="face-fallback" if self._mode(cfg) == "eyes_ipd" else "face",
                ipd=None,
            )

        if bool(cfg.fast_roi_tracking) and previous is not None and self.lost_frames < 20:
            margin = _clamp(float(cfg.face_roi_margin), 1.4, 6.0)
            side = max(previous.box_size, float(min_face_full)) * margin
            x1 = int(round(previous.cx - side / 2.0))
            y1 = int(round(previous.cy - side / 2.0))
            x2 = int(round(previous.cx + side / 2.0))
            y2 = int(round(previous.cy + side / 2.0))
            x1 = int(_clamp(x1, 0, max(0, w - 1)))
            y1 = int(_clamp(y1, 0, max(0, h - 1)))
            x2 = int(_clamp(x2, x1 + 1, w))
            y2 = int(_clamp(y2, y1 + 1, h))
            found = detect_in_region(frame_bgr[y1:y2, x1:x2], x1, y1, previous)
            if found is not None:
                return found

        return detect_in_region(frame_bgr, 0, 0, previous)

    @staticmethod
    def _choose_best_face(faces, previous_face: Optional[FaceBox]) -> Optional[FaceBox]:
        if faces is None or len(faces) == 0:
            return None
        boxes = [FaceBox(float(x), float(y), float(w), float(h)) for x, y, w, h in faces]
        if previous_face is None:
            return max(boxes, key=lambda b: b.w * b.h)

        def score(box: FaceBox) -> float:
            dist = hypot(box.cx - previous_face.cx, box.cy - previous_face.cy)
            area_bonus = 0.001 * box.w * box.h
            return dist - area_bonus

        return min(boxes, key=score)

    def _smooth_box(self, old: Optional[FaceBox], new: FaceBox, cfg: FaceDirectorConfig) -> FaceBox:
        if old is None:
            return new
        kp = self._pos_alpha(cfg)
        kz = self._scale_alpha(cfg)
        anchor_x = None
        anchor_y = None
        if old.anchor_x is not None or new.anchor_x is not None:
            ox = old.anchor_x if old.anchor_x is not None else old.cx
            nx = new.anchor_x if new.anchor_x is not None else new.cx
            anchor_x = _lerp(float(ox), float(nx), kp)
        if old.anchor_y is not None or new.anchor_y is not None:
            oy = old.anchor_y if old.anchor_y is not None else old.cy
            ny = new.anchor_y if new.anchor_y is not None else new.cy
            anchor_y = _lerp(float(oy), float(ny), kp)

        old_scale = old.scale_size if old.scale_size is not None else old.box_size
        new_scale = new.scale_size if new.scale_size is not None else new.box_size
        smoothed_scale = _lerp(float(old_scale), float(new_scale), kz)

        # x/y position follows position smoothing; box dimensions follow scale smoothing.
        return FaceBox(
            _lerp(old.x, new.x, kp),
            _lerp(old.y, new.y, kp),
            _lerp(old.w, new.w, kz),
            _lerp(old.h, new.h, kz),
            anchor_x,
            anchor_y,
            smoothed_scale,
            new.scale_source,
            new.ipd,
        )

    def _smooth_circle(self, old: Optional[CircleState], new: CircleState, cfg: FaceDirectorConfig) -> CircleState:
        if old is None:
            return new
        kp = self._pos_alpha(cfg)
        kz = self._scale_alpha(cfg)
        return CircleState(
            _lerp(old.cx, new.cx, kp),
            _lerp(old.cy, new.cy, kp),
            _lerp(old.diameter, new.diameter, kz),
        )

    def _circle_from_face(self, face: FaceBox, cfg: FaceDirectorConfig, frame_shape) -> CircleState:
        diameter = self._diameter_from_face(face, cfg, frame_shape)
        cx = face.cx - float(cfg.offset_x) * diameter + float(cfg.circle_offset_x) * diameter
        cy = face.cy - float(cfg.offset_y) * diameter + float(cfg.circle_offset_y) * diameter
        return CircleState(cx, cy, diameter)

    @staticmethod
    def _target_face_point(circle: CircleState, cfg: FaceDirectorConfig) -> tuple[float, float]:
        return (
            float(circle.cx) + (float(cfg.offset_x) - float(cfg.circle_offset_x)) * float(circle.diameter),
            float(circle.cy) + (float(cfg.offset_y) - float(cfg.circle_offset_y)) * float(circle.diameter),
        )

    def _apply_dead_zones(
        self,
        current: Optional[CircleState],
        target: CircleState,
        face: FaceBox,
        cfg: FaceDirectorConfig,
    ) -> CircleState:
        if current is None:
            return target

        pos_zone_ratio = self._pos_dead(cfg)
        scale_zone_ratio = self._scale_dead(cfg)

        cx = float(current.cx)
        cy = float(current.cy)
        diameter = float(current.diameter)

        if pos_zone_ratio <= 0.0:
            cx, cy = float(target.cx), float(target.cy)
        else:
            center_limit = max(1.0, float(current.diameter) * pos_zone_ratio)
            desired_face_cx, desired_face_cy = self._target_face_point(current, cfg)
            dx = float(face.cx - desired_face_cx)
            dy = float(face.cy - desired_face_cy)
            if abs(dx) > center_limit:
                cx += dx - (center_limit if dx > 0 else -center_limit)
            if abs(dy) > center_limit:
                cy += dy - (center_limit if dy > 0 else -center_limit)

        if scale_zone_ratio <= 0.0:
            diameter = float(target.diameter)
        else:
            diameter_limit = max(1.0, float(current.diameter) * scale_zone_ratio)
            dd = float(target.diameter - current.diameter)
            if abs(dd) > diameter_limit:
                diameter += dd - (diameter_limit if dd > 0 else -diameter_limit)

        return CircleState(cx, cy, diameter)

    @staticmethod
    def _return_circle_to_frame_center(frame_bgr: np.ndarray, circle: CircleState, cfg: FaceDirectorConfig) -> CircleState:
        speed = _clamp(float(cfg.return_speed), 0.0, 1.0)
        if speed <= 0.0:
            return circle
        h, w = frame_bgr.shape[:2]
        return CircleState(
            circle.cx + (w / 2.0 - circle.cx) * speed,
            circle.cy + (h / 2.0 - circle.cy) * speed,
            circle.diameter,
        )

    @staticmethod
    def _crop_rect_from_circle(circle: CircleState, cfg: FaceDirectorConfig) -> list[int]:
        side = max(80, int(round(circle.diameter * float(cfg.crop_padding))))
        x1 = int(round(circle.cx - side / 2.0))
        y1 = int(round(circle.cy - side / 2.0))
        return [x1, y1, side, side]

    @staticmethod
    def _crop_rect_with_padding(frame_bgr: np.ndarray, rect: list[int], return_alpha: bool = False):
        if frame_bgr is None or rect is None:
            return None
        h, w = frame_bgr.shape[:2]
        x1, y1, rw, rh = [int(v) for v in rect]
        rw = max(1, rw)
        rh = max(1, rh)
        x2 = x1 + rw
        y2 = y1 + rh
        padded = cv2.copyMakeBorder(
            frame_bgr,
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
            return (None, None) if return_alpha else None

        if not return_alpha:
            return crop.copy()

        alpha = np.zeros((rh, rw), dtype=np.uint8)
        ix1 = max(0, x1)
        iy1 = max(0, y1)
        ix2 = min(w, x2)
        iy2 = min(h, y2)
        if ix2 > ix1 and iy2 > iy1:
            dx1 = ix1 - x1
            dy1 = iy1 - y1
            dx2 = dx1 + (ix2 - ix1)
            dy2 = dy1 + (iy2 - iy1)
            alpha[dy1:dy2, dx1:dx2] = 255
        return crop.copy(), alpha

    def _draw_debug(self, crop_bgr: np.ndarray, cfg: FaceDirectorConfig) -> np.ndarray:
        if crop_bgr is None or self.crop_rect is None:
            return crop_bgr
        out = crop_bgr.copy()
        x1, y1, _rw, _rh = [int(v) for v in self.crop_rect]

        if self.circle is not None:
            ccx = int(round(self.circle.cx - x1))
            ccy = int(round(self.circle.cy - y1))
            radius = max(1, int(round(self.circle.diameter / 2.0)))
            cv2.circle(out, (ccx, ccy), radius, (0, 220, 255), 2)
            cv2.line(out, (ccx - 10, ccy), (ccx + 10, ccy), (0, 220, 255), 1)
            cv2.line(out, (ccx, ccy - 10), (ccx, ccy + 10), (0, 220, 255), 1)

            txf, tyf = self._target_face_point(self.circle, cfg)
            tx = int(round(txf - x1))
            ty = int(round(tyf - y1))
            pzone = int(round(self.circle.diameter * self._pos_dead(cfg)))
            if pzone > 0:
                cv2.rectangle(out, (tx - pzone, ty - pzone), (tx + pzone, ty + pzone), (120, 120, 120), 1)
            cv2.circle(out, (tx, ty), 6, (255, 180, 80), -1)
            cv2.circle(out, (tx, ty), 12, (255, 180, 80), 1)

        if self.face is not None:
            fx1 = int(round(self.face.x - x1))
            fy1 = int(round(self.face.y - y1))
            fx2 = int(round(self.face.x + self.face.w - x1))
            fy2 = int(round(self.face.y + self.face.h - y1))
            cv2.rectangle(out, (fx1, fy1), (fx2, fy2), (255, 168, 46), 1)
            cv2.circle(out, (int(round(self.face.cx - x1)), int(round(self.face.cy - y1))), 4, (80, 220, 255), -1)

        if self._last_landmarks:
            for x, y in self._last_landmarks:
                px = int(round(x - x1))
                py = int(round(y - y1))
                if 0 <= px < out.shape[1] and 0 <= py < out.shape[0]:
                    cv2.circle(out, (px, py), 1, (130, 255, 130), -1)

        scale_src = self._last_scale_source
        text = (
            f"director: {'FACE' if self.face_found else 'LAST / NO FACE'} | {self._last_backend} | "
            f"mode={self._mode(cfg)} zoom={self._zoom_mode(cfg)} scale={scale_src} "
            f"posSmooth={self._pos_alpha(cfg):.2f} scaleSmooth={self._scale_alpha(cfg):.2f} "
            f"posZone={self._pos_dead(cfg):.2f} scaleZone={self._scale_dead(cfg):.2f}"
        )
        cv2.putText(
            out,
            text,
            (10, max(24, out.shape[0] - 16)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.43,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )
        return out
