import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.data_processor import haversine

class TestHaversine:

    def test_same_point_is_zero(self):
        assert haversine(52.23, 21.01, 52.23, 21.01) == 0

    def test_warszawa_krakow(self):
        dist = haversine(52.2297, 21.0122, 50.0647, 19.9450)
        assert 240 < dist < 270

    def test_is_symmetric(self):
        dist1 = haversine(52.23, 21.01, 50.06, 19.94)
        dist2 = haversine(50.06, 19.94, 52.23, 21.01)
        assert abs(dist1 - dist2) < 0.001

    def test_returns_kilometers(self):
        dist = haversine(52.2297, 21.0122, 50.0647, 19.9450)
        assert dist < 10000  # gdyby bylo w metrach byloby 250000
