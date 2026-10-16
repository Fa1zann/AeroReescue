"""
modules/victim_detection.py
OVERWATCH2 aerial flood-water segmentation.

This module detects visible water only. Victim detection and person-size
estimation are intentionally not implemented. The legacy function name
analyze_victim_imagery is retained temporarily so existing app.py imports do
not break; it returns water-analysis results only.

Important: colour-based segmentation is a heuristic. Green vegetation, roofs,
shadows, and reflections may still cause false positives/negatives. A trained
segmentation model and representative labelled drone images are needed for
reliable operational use.
"""

from __future__ import annotations

import cv2
import numpy as np
import streamlit as st


def init_victim_state():
    """Legacy compatibility only; no victim detections are performed."""
    if "victim_detections" not in st.session_state:
        st.session_state["victim_detections"] = []


def _decode_image_bytes(image_bytes):
    raw = np.frombuffer(image_bytes or b"", dtype=np.uint8)
    if raw.size == 0:
        return None
    return cv2.imdecode(raw, cv2.IMREAD_COLOR)


def _odd_kernel(value, maximum=15):
    value = max(3, min(int(value), maximum))
    return value if value % 2 else value + 1


def detect_flood_water_mask(img_bgr, min_component_ratio=0.00008):
    """
    Return (mask, flood_percentage), where mask is uint8 (water=255).

    Strategy:
      * combine broad HSV water-colour bands for teal, green/murky, and muddy
        water rather than relying on one narrow hue range;
      * add a LAB colour check to recover some water affected by white balance;
      * suppress only very bright, low-saturation glare;
      * use modest morphology and a low component-area cutoff so small pools
        and narrow water channels are not discarded.

    Do not interpret the percentage as geographic flood coverage: it is the
    percentage of pixels in this image classified as water.
    """
    if img_bgr is None or not isinstance(img_bgr, np.ndarray) or img_bgr.size == 0:
        raise ValueError("Image is empty or invalid.")
    if img_bgr.ndim == 2:
        img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_GRAY2BGR)
    elif img_bgr.ndim == 3 and img_bgr.shape[2] == 4:
        img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2BGR)
    elif img_bgr.ndim != 3 or img_bgr.shape[2] != 3:
        raise ValueError("Expected a grayscale, BGR, or BGRA image.")

    h, w = img_bgr.shape[:2]
    total_pixels = max(1, h * w)

    # Mild smoothing reduces compression noise without blurring large regions.
    smooth = cv2.GaussianBlur(img_bgr, (5, 5), 0)
    hsv = cv2.cvtColor(smooth, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(smooth, cv2.COLOR_BGR2LAB)

    H, S, V = cv2.split(hsv)
    L, A, B = cv2.split(lab)

    # OpenCV hue uses 0..179, not 0..360.
    # Floodwater varies significantly with camera, turbidity, and sunlight.
    teal = (
        (H >= 68) & (H <= 112) &
        (S >= 18) & (V >= 28) & (V <= 242)
    )

    green_murky = (
        (H >= 34) & (H <= 82) &
        (S >= 16) & (S <= 170) &
        (V >= 28) & (V <= 205)
    )

    muddy_or_silty = (
        (H >= 7) & (H <= 29) &
        (S >= 22) & (V >= 28) & (V <= 190)
    )

    # LAB fallback: water can shift hue under shadows/white balance. Keep this
    # band intentionally restrained because LAB alone can select vegetation.
    lab_blue_green = (
        (A >= 105) & (A <= 145) &
        (B >= 105) & (B <= 155) &
        (L >= 25) & (L <= 190) &
        (S >= 12)
    )

    candidate = teal | green_murky | muddy_or_silty | lab_blue_green

    # Remove near-white sun glare, not all bright pixels. The previous approach
    # used dilated Canny edges and erased legitimate water near every structure.
    glare = (V >= 228) & (S <= 34)
    candidate &= ~glare

    # Extremely dark, nearly neutral pixels have unreliable colour information.
    candidate &= ~((V < 22) & (S < 50))

    mask = candidate.astype(np.uint8) * 255

    # Morphology should join small breaks without swallowing narrow waterways.
    kernel_size = _odd_kernel(round(min(h, w) * 0.004), maximum=11)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Keep smaller connected areas than the original 0.2% frame threshold.
    minimum_area = max(10, int(total_pixels * max(0.0, min_component_ratio)))
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )
    cleaned = np.zeros_like(mask)
    for label in range(1, component_count):
        if stats[label, cv2.CC_STAT_AREA] >= minimum_area:
            cleaned[labels == label] = 255

    water_pixels = cv2.countNonZero(cleaned)
    percentage = round(100.0 * water_pixels / total_pixels, 2)
    return cleaned, percentage


def _severity_from_percentage(flood_percentage):
    """Simple image-coverage indicator, not a real-world flood-risk score."""
    pct = max(0.0, min(100.0, float(flood_percentage)))
    if pct < 30:
        score = pct * 1.5
    else:
        score = 40 + pct * 0.8
    return int(max(0, min(100, round(score))))


def _overlay_water(img_bgr, water_mask, alpha=0.38):
    """Blend cyan over detected water and draw a clear boundary."""
    overlay = img_bgr.copy()
    cyan = np.zeros_like(img_bgr)
    cyan[:] = (255, 220, 0)  # BGR cyan
    selected = cv2.bitwise_and(cyan, cyan, mask=water_mask)
    overlay = cv2.addWeighted(overlay, 1.0, selected, alpha, 0)
    contours, _ = cv2.findContours(
        water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(overlay, contours, -1, (255, 190, 0), 2)
    return overlay


def analyze_victim_imagery(
    img_bytes,
    lat=None,
    lon=None,
    sector_name="Unknown sector",
    sensitivity=70.0,
    target_size=None,
    use_sahi=False,
    apply_scene_mask=False,
    dedupe_iou=0.20,
):
    """
    Legacy-compatible entry point for existing imports.

    `target_size` is accepted only for backward compatibility and is ignored.
    No person-size estimation or victim detection is performed.
    """
    init_victim_state()
    img_bgr = _decode_image_bytes(img_bytes)
    if img_bgr is None:
        return {
            "error": "Corrupt or missing image file.",
            "annotated_image": None,
            "flood_percentage": 0.0,
            "calculated_severity": 0,
        }

    mask, flood_percentage = detect_flood_water_mask(img_bgr)
    annotated_bgr = _overlay_water(img_bgr, mask)
    return {
        "annotated_image": cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB),
        "flood_percentage": flood_percentage,
        "calculated_severity": _severity_from_percentage(flood_percentage),
        "water_mask": mask,
        "water_surface_type": "Heuristic surface-water segmentation",
        "sector_name": sector_name,
        "latitude": lat,
        "longitude": lon,
    }


def analyze_aerial_image(image_bytes):
    """Analyse an uploaded aerial image and return a JPEG overlay plus metrics."""
    img_bgr = _decode_image_bytes(image_bytes)
    if img_bgr is None:
        raise ValueError("Could not decode image. Upload a valid JPG or PNG.")

    mask, flood_percentage = detect_flood_water_mask(img_bgr)
    overlay_bgr = _overlay_water(img_bgr, mask)
    ok, encoded = cv2.imencode(
        ".jpg", overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92]
    )
    if not ok:
        raise RuntimeError("Could not encode processed image.")

    return {
        "processed_image": encoded.tobytes(),
        "flood_percentage": flood_percentage,
        "calculated_severity": _severity_from_percentage(flood_percentage),
        "confidence_score": None,
        "water_surface_type": "Heuristic surface flood-water segmentation",
        "water_mask": mask,
    }


# Retained only to avoid breaking older imports elsewhere in the application.
def log_detections(new_detections, lat, lon, existing):
    return []


def add_victim_layer_to_map(m, detections):
    return m
