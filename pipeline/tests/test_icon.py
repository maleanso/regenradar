from datetime import datetime, timedelta, timezone

import eccodes
import numpy as np
import pytest

from regenradar import icon
from regenradar.grid import TargetGrid

RUN = datetime(2026, 11, 27, 6, tzinfo=timezone.utc)


def test_parse_horizon():
    assert icon.parse_horizon("P0DT06H00M00S") == 6
    assert icon.parse_horizon("P1DT09H00M00S") == 33
    with pytest.raises(ValueError):
        icon.parse_horizon("P0DT00H30M00S")


def test_hourly_difference():
    prev = np.array([0.0, 1.0, 2.0])
    cur = np.array([0.5, 1.0, 1.9999])  # tiny negative from packing → 0
    assert icon.hourly(prev, cur).tolist() == [0.5, 0.0, 0.0]
    assert icon.hourly(None, cur).tolist() == cur.tolist()


def test_frames_cover_now_to_six_hours():
    now = datetime(2026, 11, 27, 10, 9, tzinfo=timezone.utc)
    frames = icon.frames_for(RUN, now, timedelta(hours=6))
    assert [f.horizon for f in frames] == [5, 6, 7, 8, 9, 10, 11]
    assert frames[0].start == RUN + timedelta(hours=4) and frames[0].end == datetime(2026, 11, 27, 11, tzinfo=timezone.utc)
    later = icon.frames_for(RUN, now, timedelta(hours=6), start_after=timedelta(hours=2))
    assert later[0].end > now + timedelta(hours=2)


def test_build_index_nearest_and_distance_limit():
    g = TargetGrid(west=7.0, south=46.0, east=7.2, north=46.2, pixel_m=5000)
    lon = np.array([7.05, 7.15, 30.0])
    lat = np.array([46.1, 46.1, 10.0])
    idx, valid = icon.build_index(lon, lat, g)
    assert idx.shape == (g.height, g.width)
    assert set(np.unique(idx[valid])) <= {0, 1}
    assert idx[0, 0] == 0 and idx[0, -1] == 1


def _sample_grib(units_ok: bool) -> bytes:
    h = eccodes.codes_grib_new_from_samples("GRIB2")
    try:
        if units_ok:
            # accumulated total precipitation in kg m-2 (as in ICON-CH1 files)
            eccodes.codes_set(h, "productDefinitionTemplateNumber", 8)
            eccodes.codes_set(h, "discipline", 0)
            eccodes.codes_set(h, "parameterCategory", 1)
            eccodes.codes_set(h, "parameterNumber", 52)
            eccodes.codes_set_string(h, "stepType", "accum")
        return eccodes.codes_get_message(h)
    finally:
        eccodes.codes_release(h)


def test_split_messages_and_unit_check():
    msg = _sample_grib(units_ok=False)
    assert icon.split_messages(msg + msg) == [msg, msg]
    with pytest.raises(ValueError, match="unit"):
        icon.read_values(msg)  # sample is temperature (K)


def test_read_values_tp():
    msg = _sample_grib(units_ok=True)
    vals, uuid = icon.read_values(msg)
    assert vals.size > 0
    assert isinstance(uuid, str)
