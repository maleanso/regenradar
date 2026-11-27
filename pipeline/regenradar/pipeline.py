"""One pipeline run: new radar frames, newest ICON run, index.json, clean-up."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from . import __version__, http, icon, radar
from .colors import legend
from .grid import TargetGrid
from .render import to_png
from .store import INDEX_CACHE, PNG_CACHE, Store

SOURCE = "Source: MeteoSwiss"
DISCLAIMER = "Kein offizielles Flugwetterprodukt – nur für Versuchszwecke."
_STAMP = "%Y%m%dT%H%MZ"
_RADAR_KEY = re.compile(r"^radar/(\d{8}T\d{4}Z)\.png$")
_MODEL_KEY = re.compile(r"^model/(\d{8}T\d{4}Z)/(\d{8}T\d{4}Z)\.png$")


def iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime(_STAMP)


def unstamp(s: str) -> datetime:
    return datetime.strptime(s, _STAMP).replace(tzinfo=timezone.utc)


def radar_key(t: datetime) -> str:
    return f"radar/{stamp(t)}.png"


def model_key(run: datetime, end: datetime) -> str:
    return f"model/{stamp(run)}/{stamp(end)}.png"


@dataclass
class Settings:
    history: timedelta = timedelta(hours=3)
    ahead: timedelta = timedelta(hours=6)
    # Model frames start right after "now" until the own radar extrapolation exists (ADR 0002: later +2 h).
    model_start: timedelta = timedelta(0)
    keep_margin: timedelta = timedelta(minutes=15)
    grid: TargetGrid = field(default_factory=TargetGrid)


@dataclass
class Report:
    radar_new: int = 0
    radar_errors: int = 0
    model_new: int = 0
    model_run: datetime | None = None
    deleted: int = 0
    notes: list[str] = field(default_factory=list)


def update_radar(store: Store, now: datetime, s: Settings, cache: Path, rep: Report) -> None:
    existing = store.keys("radar/")
    for f in radar.list_files(now - s.history, now):
        key = radar_key(f.time)
        if key in existing:
            continue
        try:
            fld = radar.read_field(http.get_bytes(f.href))
            if fld.time != f.time:
                rep.notes.append(f"radar {f.name}: file time {iso(fld.time)} differs from name")
            store.put(radar_key(fld.time), to_png(radar.resample(fld, s.grid, cache)), "image/png", PNG_CACHE)
            rep.radar_new += 1
        except Exception as exc:  # one broken file must not stop the run
            rep.radar_errors += 1
            rep.notes.append(f"radar {f.name}: {exc}")


def _needed_horizons(frames: list[icon.ModelFrame]) -> set[int]:
    need = set()
    for fr in frames:
        need.add(fr.horizon)
        if fr.horizon > 1:
            need.add(fr.horizon - 1)
    return need


def choose_run(now: datetime, s: Settings) -> tuple[datetime, dict[int, str], list[icon.ModelFrame]] | None:
    """Newest run that has every horizon needed for the frames between now and now + ahead."""
    feats = icon._search({"forecast:horizon": "P0DT01H00M00S"})
    runs = sorted({icon._parse_time(f["properties"]["forecast:reference_datetime"]) for f in feats}, reverse=True)
    for run in runs[:3]:
        frames = icon.frames_for(run, now, s.ahead, s.model_start)
        if not frames:
            continue
        files = icon.run_files(run)
        if _needed_horizons(frames) <= set(files):
            return run, files, frames
    return None


def update_model(store: Store, now: datetime, s: Settings, cache: Path, rep: Report) -> datetime | None:
    chosen = choose_run(now, s)
    if chosen is None:
        rep.notes.append("model: no complete ICON-CH1 run found")
        return None
    run, files, frames = chosen
    existing = store.keys(f"model/{stamp(run)}/")
    regrid = icon.Regridder(s.grid, cache)
    values: dict[int, np.ndarray] = {}

    def load(h: int) -> np.ndarray:
        if h not in values:
            vals, uuid = icon.read_values(http.get_bytes(files[h]))
            regrid.prepare(uuid)
            values[h] = vals
        return values[h]

    for fr in frames:
        key = model_key(run, fr.end)
        if key in existing:
            continue
        prev = load(fr.horizon - 1) if fr.horizon > 1 else None
        rate = icon.hourly(prev, load(fr.horizon))
        store.put(key, to_png(regrid.apply(rate)), "image/png", PNG_CACHE)
        rep.model_new += 1
    rep.model_run = run
    return run


def build_index(store: Store, now: datetime, s: Settings, run: datetime | None) -> dict:
    frames = []
    radar_times = []
    for key in store.keys("radar/"):
        m = _RADAR_KEY.match(key)
        if m:
            t = unstamp(m.group(1))
            if now - s.history <= t <= now:
                radar_times.append(t)
    for t in sorted(radar_times):
        frames.append({"time": iso(t), "from": iso(t - timedelta(minutes=5)), "kind": "radar", "url": radar_key(t)})

    model = None
    if run is not None:
        ends = []
        for key in store.keys(f"model/{stamp(run)}/"):
            m = _MODEL_KEY.match(key)
            if m:
                end = unstamp(m.group(2))
                if end > now + s.model_start and end - timedelta(hours=1) < now + s.ahead:
                    ends.append(end)
        for end in sorted(ends):
            frames.append({"time": iso(end), "from": iso(end - timedelta(hours=1)), "kind": "model", "url": model_key(run, end)})
        model = {"name": "ICON-CH1-EPS (Kontrolllauf)", "run": iso(run), "interval_min": 60,
                 "note": "Stundenmittel aus dem Modell, keine Messung"}

    return {
        "version": 1,
        "generator": f"regenradar {__version__}",
        "generated": iso(now),
        "source": SOURCE,
        "disclaimer": DISCLAIMER,
        "crs": "EPSG:3857",
        "bounds": s.grid.bounds_latlon(),
        "size": [s.grid.width, s.grid.height],
        "legend": legend(),
        "unit": "mm/h",
        "radar": {"latest": iso(max(radar_times)) if radar_times else None, "interval_min": 5,
                  "note": "Momentane Regenrate aus dem Radar-Komposit (PRECIP)"},
        "model": model,
        "frames": frames,
    }


def prune(store: Store, now: datetime, s: Settings, run: datetime | None) -> int:
    old = []
    limit = now - s.history - s.keep_margin
    for key in store.keys("radar/"):
        m = _RADAR_KEY.match(key)
        if m and unstamp(m.group(1)) < limit:
            old.append(key)
    if run is not None:  # keep model frames only for the run that is in use
        keep = f"model/{stamp(run)}/"
        old.extend(k for k in store.keys("model/") if not k.startswith(keep))
    if old:
        store.delete(sorted(old))
    return len(old)


def run_once(store: Store, cache: Path, now: datetime | None = None, s: Settings | None = None,
             with_model: bool = True) -> Report:
    now = now or datetime.now(timezone.utc)
    s = s or Settings()
    rep = Report()
    update_radar(store, now, s, cache, rep)
    run = None
    if with_model:
        try:
            run = update_model(store, now, s, cache, rep)
        except Exception as exc:
            rep.notes.append(f"model: {exc}")
        if run is None:
            run = newest_stored_run(store, now)
            if run is not None:
                rep.notes.append(f"model: keeping stored run {iso(run)}")
    index = build_index(store, now, s, run)
    store.put("index.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")).encode(),
              "application/json; charset=utf-8", INDEX_CACHE)
    rep.deleted = prune(store, now, s, run)
    return rep


def newest_stored_run(store: Store, now: datetime) -> datetime | None:
    runs = set()
    for key in store.keys("model/"):
        m = _MODEL_KEY.match(key)
        if m and unstamp(m.group(2)) > now:
            runs.add(unstamp(m.group(1)))
    return max(runs) if runs else None
