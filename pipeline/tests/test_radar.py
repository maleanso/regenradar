from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from pyproj import Transformer

from regenradar import radar
from regenradar.grid import TargetGrid

SAMPLE = Path(__file__).parent / "data" / "rzc263310955vl.001.h5"


def test_parse_name():
    assert radar.parse_name("rzc263310955vl.001.h5") == datetime(2026, 11, 27, 9, 55, tzinfo=timezone.utc)
    assert radar.parse_name("RZC260010000VL.801.h5") == datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert radar.parse_name("cpc2631500002_00060.001.h5") is None


def test_files_from_item_ignores_other_products():
    item = {"assets": {
        "rzc263310955vl.001.h5": {"href": "https://x/a.h5"},
        "cpc263310950_00060.001.h5": {"href": "https://x/b.h5"},
        "tzc263310955vl.001.h5": {"href": "https://x/c.h5"},
    }}
    files = radar.files_from_item(item)
    assert [f.name for f in files] == ["rzc263310955vl.001.h5"]


def test_read_real_file():
    f = radar.read_field(SAMPLE.read_bytes())
    assert f.time == datetime(2026, 11, 27, 9, 55, tzinfo=timezone.utc)
    assert f.rate.shape == (640, 710)
    assert (f.x0, f.y0, f.dx, f.dy) == (2255000.0, 1480000.0, 1000.0, 1000.0)
    assert np.isnan(f.rate).any() and (f.rate == 0).any()
    assert np.nanmax(f.rate) < 118.0001


def test_resample_hits_the_right_pixel(tmp_path):
    """Bern (LV95 2600000/1200000) must land in radar column 345, row 280."""
    f = radar.read_field(SAMPLE.read_bytes())
    marked = f.rate.copy()
    marked[:] = 0.0
    marked[280, 345] = 50.0
    f = radar.RadarField(f.time, marked, f.x0, f.y0, f.dx, f.dy)
    g = TargetGrid()
    out = radar.resample(f, g, tmp_path)
    to_merc = Transformer.from_crs("EPSG:2056", "EPSG:3857", always_xy=True)
    x, y = to_merc.transform(2600500, 1199500)  # centre of that radar pixel
    xmin, _, _, ymax = g.extent
    col = int((x - xmin) // g.pixel_m)
    row = int((ymax - y) // g.pixel_m)
    assert out[row, col] == 50.0
    assert (out == 50.0).sum() in range(1, 5)  # one radar km ≈ 2×2 target pixels
    # cached index gives the same result
    assert np.array_equal(radar.resample(f, g, tmp_path), out, equal_nan=True)


def test_outside_radar_area_is_nan(tmp_path):
    f = radar.read_field(SAMPLE.read_bytes())
    g = TargetGrid(west=0.0, south=42.0, east=3.0, north=43.0)  # south-west of the composite
    assert np.isnan(radar.resample(f, g, tmp_path)).all()
