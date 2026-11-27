import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from regenradar import http, pipeline, radar
from regenradar.pipeline import Settings, model_key, radar_key, run_once
from regenradar.store import LocalStore

SAMPLE = Path(__file__).parent / "data" / "rzc263310955vl.001.h5"
NOW = datetime(2026, 11, 27, 10, 0, 30, tzinfo=timezone.utc)
RUN = datetime(2026, 11, 27, 6, tzinfo=timezone.utc)


def _fake_radar(monkeypatch):
    t = datetime(2026, 11, 27, 9, 55, tzinfo=timezone.utc)
    files = [radar.RadarFile(t, "rzc263310955vl.001.h5", "https://example/rzc.h5")]
    monkeypatch.setattr(radar, "list_files", lambda start, end: [f for f in files if start <= f.time <= end])
    monkeypatch.setattr(http, "get_bytes", lambda url: SAMPLE.read_bytes())


def test_radar_only_run_writes_frames_and_index(tmp_path, monkeypatch):
    _fake_radar(monkeypatch)
    store = LocalStore(tmp_path / "out")
    old = radar_key(NOW - timedelta(hours=4))
    store.put(old, b"x", "image/png", "")
    rep = run_once(store, tmp_path / "cache", now=NOW, with_model=False)
    assert rep.radar_new == 1 and rep.radar_errors == 0
    assert rep.deleted == 1 and old not in store.keys("radar/")
    idx = json.loads((tmp_path / "out" / "index.json").read_text())
    assert idx["source"] == "Source: MeteoSwiss"
    assert "Versuchszwecke" in idx["disclaimer"]
    assert idx["radar"]["latest"] == "2026-11-27T09:55:00Z"
    assert idx["model"] is None
    assert idx["frames"] == [{"time": "2026-11-27T09:55:00Z", "from": "2026-11-27T09:50:00Z",
                              "kind": "radar", "url": "radar/20261127T0955Z.png"}]
    assert (tmp_path / "out" / "radar" / "20261127T0955Z.png").read_bytes()[:4] == b"\x89PNG"
    # second run: nothing new
    assert run_once(store, tmp_path / "cache", now=NOW, with_model=False).radar_new == 0


def test_index_lists_model_frames_of_the_chosen_run_and_prunes_old_runs(tmp_path):
    store = LocalStore(tmp_path)
    s = Settings()
    for h in range(4, 13):
        store.put(model_key(RUN, RUN + timedelta(hours=h)), b"x", "image/png", "")
    old_run = RUN - timedelta(hours=3)
    store.put(model_key(old_run, NOW + timedelta(hours=1)), b"x", "image/png", "")
    idx = pipeline.build_index(store, NOW, s, RUN)
    model = [f for f in idx["frames"] if f["kind"] == "model"]
    # frames ending after now and starting before now + 6 h (16:00:30): 11:00 … 17:00 UTC
    assert [f["time"][11:16] for f in model] == ["11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    assert model[0]["from"] == "2026-11-27T10:00:00Z"
    assert idx["model"]["run"] == "2026-11-27T06:00:00Z"
    assert pipeline.prune(store, NOW, s, RUN) == 1
    assert pipeline.newest_stored_run(store, NOW) == RUN


def test_model_failure_keeps_stored_run(tmp_path, monkeypatch):
    _fake_radar(monkeypatch)
    store = LocalStore(tmp_path)
    store.put(model_key(RUN, NOW + timedelta(hours=1)), b"x", "image/png", "")

    def boom(*a, **k):
        raise RuntimeError("STAC down")

    monkeypatch.setattr(pipeline, "choose_run", boom)
    rep = run_once(store, tmp_path / "cache", now=NOW)
    assert any("STAC down" in n for n in rep.notes)
    idx = json.loads((tmp_path / "index.json").read_text())
    assert idx["model"]["run"] == "2026-11-27T06:00:00Z"
