"""Target raster in Web Mercator (EPSG:3857) shared by all frames."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import numpy as np
from pyproj import Transformer

_TO_MERC = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
_TO_LONLAT = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)


@dataclass(frozen=True)
class TargetGrid:
    """Regular Web Mercator raster. Pixel edges are snapped to multiples of `pixel_m`."""

    west: float = 2.8
    south: float = 43.7
    east: float = 12.4
    north: float = 49.3
    pixel_m: float = 720.0  # mercator metres; ~500 m on the ground at 46.5° N

    @cached_property
    def extent(self) -> tuple[float, float, float, float]:
        """(xmin, ymin, xmax, ymax) in mercator metres, snapped to the pixel size."""
        x0, y0 = _TO_MERC.transform(self.west, self.south)
        x1, y1 = _TO_MERC.transform(self.east, self.north)
        p = self.pixel_m
        return (np.floor(x0 / p) * p, np.floor(y0 / p) * p, np.ceil(x1 / p) * p, np.ceil(y1 / p) * p)

    @property
    def width(self) -> int:
        xmin, _, xmax, _ = self.extent
        return int(round((xmax - xmin) / self.pixel_m))

    @property
    def height(self) -> int:
        _, ymin, _, ymax = self.extent
        return int(round((ymax - ymin) / self.pixel_m))

    def centres(self) -> tuple[np.ndarray, np.ndarray]:
        """Mercator x/y of pixel centres, shape (height, width); row 0 = north."""
        xmin, _, _, ymax = self.extent
        p = self.pixel_m
        xs = xmin + (np.arange(self.width) + 0.5) * p
        ys = ymax - (np.arange(self.height) + 0.5) * p
        return np.meshgrid(xs, ys)

    def bounds_latlon(self) -> list[list[float]]:
        """Leaflet bounds [[south, west], [north, east]] of the outer pixel edges."""
        xmin, ymin, xmax, ymax = self.extent
        w, s = _TO_LONLAT.transform(xmin, ymin)
        e, n = _TO_LONLAT.transform(xmax, ymax)
        return [[round(s, 6), round(w, 6)], [round(n, 6), round(e, 6)]]

    def key(self) -> str:
        """Identifier for cached index arrays."""
        xmin, ymin, xmax, ymax = self.extent
        return f"{int(xmin)}_{int(ymin)}_{int(xmax)}_{int(ymax)}_{int(self.pixel_m)}"
