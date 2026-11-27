"""MeteoSwiss precipitation colour scale (read from the MeteoSwiss app legend, see docs/daten.md)."""

from __future__ import annotations

import numpy as np

# (lower bound in mm/h, hex colour). Upper bound = next lower bound; last class is open-ended.
SCALE: list[tuple[float, str]] = [
    (0.2, "#9B7D96"),
    (1.0, "#0000FF"),
    (2.0, "#058C2D"),
    (4.0, "#05FF05"),
    (6.0, "#FFFF00"),
    (10.0, "#FFC800"),
    (20.0, "#FF7D00"),
    (40.0, "#FF1900"),
    (60.0, "#AF00DC"),
]

THRESHOLDS = np.array([lo for lo, _ in SCALE], dtype=np.float64)


def _rgb(hex_colour: str) -> tuple[int, int, int]:
    h = hex_colour.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def classify(rate: np.ndarray) -> np.ndarray:
    """Map mm/h to class indices: 0 = transparent (< 0.2 mm/h or no data), 1..9 = colour classes."""
    r = np.asarray(rate, dtype=np.float64)
    cls = np.searchsorted(THRESHOLDS, np.nan_to_num(r, nan=-1.0), side="right")
    return cls.astype(np.uint8)


def palette() -> list[int]:
    """Flat RGB palette for a 'P' mode PNG; index 0 is the transparent colour."""
    flat = [0, 0, 0]
    for _, colour in SCALE:
        flat.extend(_rgb(colour))
    return flat


def legend() -> list[dict]:
    """Legend for index.json."""
    out = []
    for i, (lo, colour) in enumerate(SCALE):
        hi = SCALE[i + 1][0] if i + 1 < len(SCALE) else None
        out.append({"from": lo, "to": hi, "color": colour})
    return out
