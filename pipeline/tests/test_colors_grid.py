import io

import numpy as np
from PIL import Image

from regenradar.colors import SCALE, classify, legend, palette
from regenradar.grid import TargetGrid
from regenradar.render import to_png


def test_classify_thresholds():
    vals = np.array([np.nan, 0.0, 0.19, 0.2, 0.99, 1.0, 5.9, 6.0, 59.9, 60.0, 118.0])
    assert classify(vals).tolist() == [0, 0, 0, 1, 1, 2, 4, 5, 8, 9, 9]


def test_palette_and_legend():
    assert len(palette()) == 3 * (len(SCALE) + 1)
    lg = legend()
    assert lg[0] == {"from": 0.2, "to": 1.0, "color": "#9B7D96"}
    assert lg[-1] == {"from": 60.0, "to": None, "color": "#AF00DC"}


def test_png_is_transparent_palette():
    rate = np.array([[np.nan, 0.1], [0.5, 70.0]])
    img = Image.open(io.BytesIO(to_png(rate)))
    assert img.mode == "P"
    assert img.info["transparency"] == 0
    assert np.array(img).tolist() == [[0, 0], [1, 9]]


def test_grid_covers_switzerland():
    g = TargetGrid()
    (s, w), (n, e) = g.bounds_latlon()
    assert w < 5.9 and e > 10.5 and s < 45.8 and n > 47.8
    assert g.width > 1000 and g.height > 1000
    mx, my = g.centres()
    assert mx.shape == (g.height, g.width)
    assert my[0, 0] > my[-1, 0]  # row 0 = north
