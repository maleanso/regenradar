"""ICON-CH1-EPS TOT_PREC (control run): find the latest run, build hourly mm/h fields, regrid."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import eccodes
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

from . import http
from .grid import TargetGrid

COLLECTION = "ch.meteoschweiz.ogd-forecasting-icon-ch1"
CONSTANTS_ASSET = "horizontal_constants_icon-ch1-eps.grib2"
VARIABLE = "TOT_PREC"
MAX_DIST_M = 2500.0  # mercator metres; ICON spacing ~1 km on the ground (~1.45 km in mercator)
_HORIZON = re.compile(r"^P(\d+)DT(\d+)H(\d+)M(\d+)S$")


def parse_horizon(text: str) -> int:
    """`P1DT03H00M00S` → 27 (hours)."""
    m = _HORIZON.match(text)
    if not m:
        raise ValueError(f"bad horizon {text!r}")
    d, h, mi, s = (int(g) for g in m.groups())
    if mi or s:
        raise ValueError(f"non-hourly horizon {text!r}")
    return d * 24 + h


def _parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _search(body: dict) -> list[dict]:
    body = {"collections": [COLLECTION], "forecast:variable": VARIABLE, "forecast:perturbed": False, "limit": 100, **body}
    url = f"{http.STAC_URL}/search"
    feats: list[dict] = []
    for _ in range(10):  # follow paging
        page = http.post_json(url, body)
        feats.extend(page.get("features", []))
        nxt = next((l for l in page.get("links", []) if l.get("rel") == "next"), None)
        if not nxt:
            break
        if nxt.get("method", "GET").upper() == "POST":
            body = nxt.get("body", body)
            url = nxt["href"]
        else:
            page = http.get_json(nxt["href"])
            feats.extend(page.get("features", []))
            break
    return feats


def latest_run(min_horizon: int) -> datetime | None:
    """Newest run that already offers TOT_PREC at `min_horizon` (proxy for 'run is published')."""
    feats = _search({"forecast:horizon": f"P0DT{min_horizon:02d}H00M00S"})
    runs = [_parse_time(f["properties"]["forecast:reference_datetime"]) for f in feats]
    return max(runs) if runs else None


def run_files(run: datetime) -> dict[int, str]:
    """horizon (h) → download URL for all TOT_PREC control files of one run."""
    feats = _search({"forecast:reference_datetime": run.strftime("%Y-%m-%dT%H:%M:%SZ")})
    out = {}
    for f in feats:
        h = parse_horizon(f["properties"]["forecast:horizon"])
        out[h] = next(iter(f["assets"].values()))["href"]
    return out


def read_values(data: bytes) -> tuple[np.ndarray, str]:
    """Values and uuidOfHGrid of a single-message GRIB2 file (TOT_PREC in kg m-2 = mm)."""
    h = eccodes.codes_new_from_message(data)
    try:
        units = eccodes.codes_get(h, "units")
        if units not in ("kg m**-2", "kg m-2", "mm"):
            raise ValueError(f"unexpected TOT_PREC unit {units!r}")
        vals = eccodes.codes_get_values(h).astype(np.float64)
        missing = eccodes.codes_get(h, "missingValue")
        if eccodes.codes_get(h, "bitmapPresent"):
            vals[vals == missing] = np.nan
        try:
            uuid = eccodes.codes_get(h, "uuidOfHGrid")
        except eccodes.KeyValueNotFoundError:
            uuid = ""  # only unstructured grids carry it; Regridder.prepare rejects ""
        return vals, uuid
    finally:
        eccodes.codes_release(h)


def hourly(prev: np.ndarray | None, cur: np.ndarray) -> np.ndarray:
    """mm/h for one hour from two accumulations since run start (prev None = horizon 0)."""
    rate = cur if prev is None else cur - prev
    return np.clip(rate, 0.0, None)


def split_messages(data: bytes) -> list[bytes]:
    """Split a GRIB2 byte string into messages (total length = octets 9-16 of section 0)."""
    out, pos = [], 0
    while True:
        pos = data.find(b"GRIB", pos)
        if pos < 0:
            return out
        if data[pos + 7] != 2:
            raise ValueError("only GRIB edition 2 is supported")
        length = int.from_bytes(data[pos + 8:pos + 16], "big")
        out.append(data[pos:pos + length])
        pos += length


def _read_constants(data: bytes) -> tuple[np.ndarray, np.ndarray, str]:
    """Cell centre lon/lat (shortName tlon/tlat, or clon/clat with local tables) and grid uuid."""
    lon = lat = None
    uuid = ""
    for msg in split_messages(data):
        h = eccodes.codes_new_from_message(msg)
        try:
            name = eccodes.codes_get(h, "shortName").lower()
            if name in ("tlon", "clon"):
                lon = eccodes.codes_get_values(h)
                uuid = eccodes.codes_get(h, "uuidOfHGrid")
            elif name in ("tlat", "clat"):
                lat = eccodes.codes_get_values(h)
        finally:
            eccodes.codes_release(h)
    if lon is None or lat is None:
        raise ValueError("cell centre coordinates not found in ICON constants")
    return lon, lat, uuid


class Regridder:
    """Maps the unstructured ICON grid onto the target grid (nearest cell centre), cached on disk."""

    def __init__(self, grid: TargetGrid, cache: Path):
        self.grid = grid
        self.cache = cache
        self._index: np.ndarray | None = None
        self._valid: np.ndarray | None = None
        self._uuid: str | None = None

    def _constants(self) -> tuple[np.ndarray, np.ndarray, str]:
        path = self.cache / "icon_ch1_coords.npz"
        if path.exists():
            z = np.load(path)
            return z["lon"], z["lat"], str(z["uuid"])
        coll = http.get_json(f"{http.STAC_URL}/collections/{COLLECTION}")
        data = http.get_bytes(coll["assets"][CONSTANTS_ASSET]["href"])
        lon, lat, uuid = _read_constants(data)
        self.cache.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, lon=lon, lat=lat, uuid=np.array(uuid))
        return lon, lat, uuid

    def prepare(self, uuid: str) -> None:
        if not uuid:
            raise ValueError("GRIB file has no uuidOfHGrid (not an ICON grid)")
        if self._uuid == uuid:
            return
        path = self.cache / f"icon_index_{uuid}_{self.grid.key()}.npz"
        if path.exists():
            z = np.load(path)
            self._index, self._valid = z["index"], z["valid"]
        else:
            lon, lat, cuuid = self._constants()
            if cuuid != uuid:
                # constants are not versioned; drop the cache once and retry with fresh ones
                (self.cache / "icon_ch1_coords.npz").unlink(missing_ok=True)
                lon, lat, cuuid = self._constants()
                if cuuid != uuid:
                    raise ValueError(f"ICON grid mismatch: data {uuid}, constants {cuuid}")
            self._index, self._valid = build_index(lon, lat, self.grid)
            self.cache.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(path, index=self._index, valid=self._valid)
        self._uuid = uuid

    def apply(self, values: np.ndarray) -> np.ndarray:
        out = values[self._index]
        out[~self._valid] = np.nan
        return out


def build_index(lon: np.ndarray, lat: np.ndarray, grid: TargetGrid) -> tuple[np.ndarray, np.ndarray]:
    """Nearest ICON cell for every target pixel; pixels farther than MAX_DIST_M are invalid."""
    to_merc = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x, y = to_merc.transform(lon, lat)
    tree = cKDTree(np.column_stack([x, y]))
    mx, my = grid.centres()
    dist, idx = tree.query(np.column_stack([mx.ravel(), my.ravel()]), k=1, workers=-1)
    shape = mx.shape
    return idx.reshape(shape).astype(np.int32), (dist <= MAX_DIST_M).reshape(shape)


@dataclass(frozen=True)
class ModelFrame:
    run: datetime
    horizon: int  # hours; frame covers (run + horizon - 1 h, run + horizon]

    @property
    def end(self) -> datetime:
        return self.run + timedelta(hours=self.horizon)

    @property
    def start(self) -> datetime:
        return self.end - timedelta(hours=1)


def frames_for(run: datetime, now: datetime, ahead: timedelta, start_after: timedelta = timedelta(0)) -> list[ModelFrame]:
    """Hourly frames whose interval ends after now + start_after and no later than now + ahead."""
    out = []
    for h in range(1, 34):
        f = ModelFrame(run, h)
        if f.end > now + start_after and f.start < now + ahead:
            out.append(f)
    return out
