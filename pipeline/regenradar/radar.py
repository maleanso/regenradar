"""Radar PRECIP (RZC): list files via STAC, read ODIM HDF5, resample to the target grid."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer

from . import http
from .grid import TargetGrid

COLLECTION = "ch.meteoschweiz.ogd-radar-precip"
_NAME = re.compile(r"^rzc(\d{2})(\d{3})(\d{2})(\d{2}).*\.h5$", re.IGNORECASE)


@dataclass(frozen=True)
class RadarFile:
    time: datetime  # end of the 5-minute interval, UTC
    name: str
    href: str


def parse_name(name: str) -> datetime | None:
    """`rzc263310955vl.001.h5` → 2026, day 331, 09:55 UTC."""
    m = _NAME.match(name)
    if not m:
        return None
    yy, doy, hh, mm = (int(g) for g in m.groups())
    return datetime(2000 + yy, 1, 1, tzinfo=timezone.utc) + timedelta(days=doy - 1, hours=hh, minutes=mm)


def files_from_item(item: dict) -> list[RadarFile]:
    out = []
    for name, asset in item.get("assets", {}).items():
        t = parse_name(name)
        if t is not None:
            out.append(RadarFile(t, name, asset["href"]))
    return out


def list_files(start: datetime, end: datetime) -> list[RadarFile]:
    """All RZC files with start <= time <= end (reads one STAC item per UTC day)."""
    files: dict[datetime, RadarFile] = {}
    day = start.date()
    while day <= end.date():
        url = f"{http.STAC_URL}/collections/{COLLECTION}/items/{day:%Y%m%d}-ch"
        try:
            item = http.get_json(url)
        except Exception as exc:  # missing day item must not stop the run
            print(f"radar: item {day} not available ({exc})")
            item = {}
        for f in files_from_item(item):
            if start <= f.time <= end:
                files[f.time] = f
        day += timedelta(days=1)
    return [files[t] for t in sorted(files)]


@dataclass(frozen=True)
class RadarField:
    time: datetime
    rate: np.ndarray  # mm/h, NaN = no data, shape (rows, cols), row 0 = north
    x0: float  # LV95 easting of the west edge
    y0: float  # LV95 northing of the north edge
    dx: float
    dy: float


def read_field(data: bytes) -> RadarField:
    """Read an ODIM HDF5 composite (values already in mm/h, gain 1, offset 0, nodata NaN)."""
    with h5py.File(io.BytesIO(data), "r") as f:
        what = f["dataset1/data1/what"].attrs
        raw = f["dataset1/data1/data"][()].astype(np.float64)
        gain, offset = float(what["gain"]), float(what["offset"])
        nodata, undetect = float(what["nodata"]), float(what["undetect"])
        rate = raw * gain + offset
        if not np.isnan(nodata):
            rate[raw == nodata] = np.nan
        rate[raw == undetect] = 0.0
        unit = what["unit"]
        unit = unit.decode() if isinstance(unit, bytes) else unit
        if unit != "mm/h":
            raise ValueError(f"unexpected radar unit {unit!r}")
        ds = f["dataset1/what"].attrs
        d = ds["enddate"].decode() + ds["endtime"].decode()
        t = datetime.strptime(d, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        where = f["where"].attrs
        to_lv95 = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
        x0, y0 = to_lv95.transform(float(where["UL_lon"]), float(where["UL_lat"]))
        dx, dy = float(where["xscale"]), float(where["yscale"])
    # corners are given in WGS84 with float32 precision: snap to the grid spacing
    return RadarField(t, rate, round(x0 / dx) * dx, round(y0 / dy) * dy, dx, dy)


def _index(field: RadarField, grid: TargetGrid) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mx, my = grid.centres()
    to_lv95 = Transformer.from_crs("EPSG:3857", "EPSG:2056", always_xy=True)
    e, n = to_lv95.transform(mx, my)
    col = np.floor((e - field.x0) / field.dx).astype(np.int64)
    row = np.floor((field.y0 - n) / field.dy).astype(np.int64)
    rows, cols = field.rate.shape
    inside = (col >= 0) & (col < cols) & (row >= 0) & (row < rows)
    return row.clip(0, rows - 1), col.clip(0, cols - 1), inside


def resample(field: RadarField, grid: TargetGrid, cache: Path | None = None) -> np.ndarray:
    """Nearest-neighbour resampling of the radar field onto the target grid."""
    key = f"radar_{grid.key()}_{int(field.x0)}_{int(field.y0)}_{field.rate.shape[0]}x{field.rate.shape[1]}.npz"
    path = cache / key if cache else None
    if path and path.exists():
        z = np.load(path)
        row, col, inside = z["row"], z["col"], z["inside"]
    else:
        row, col, inside = _index(field, grid)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(path, row=row.astype(np.int32), col=col.astype(np.int32), inside=inside)
    out = field.rate[row, col]
    out[~inside] = np.nan
    return out
