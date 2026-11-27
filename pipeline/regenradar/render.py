"""Render mm/h arrays (already on the target grid) as small palette PNGs."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from .colors import classify, palette


def to_png(rate: np.ndarray) -> bytes:
    """Palette PNG: index 0 fully transparent, 1..9 = MeteoSwiss colours (opaque)."""
    cls = classify(rate)
    img = Image.fromarray(cls, mode="P")
    img.putpalette(palette())
    buf = io.BytesIO()
    img.save(buf, format="PNG", transparency=0, optimize=True)
    return buf.getvalue()
