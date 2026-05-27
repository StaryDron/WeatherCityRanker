import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

with patch('psycopg2.connect') as mock_conn:
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    from backend.main import app

client = TestClient(app)

class TestCitiesEndpoint:

    def test_cities_returns_200(self):
        with patch('backend.main.get_db') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                (1, 'Warszawa', 52.2297, 21.0122),
                (2, 'Krakow', 50.0647, 19.9450)
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            response = client.get("/api/cities")
            assert response.status_code == 200

    def test_cities_returns_list(self):
        with patch('backend.main.get_db') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                (1, 'Warszawa', 52.2297, 21.0122)
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            response = client.get("/api/cities")
            data = response.json()
            assert "cities" in data
            assert len(data["cities"]) == 1
            assert data["cities"][0]["name"] == "Warszawa"

class TestRankingEndpoint:

    def test_ranking_returns_200(self):
        with patch('backend.main.get_db') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                (1, 'Warszawa', 7, 85),
                (2, 'Krakow', 5, 75)
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            response = client.get("/api/cities/ranking")
            assert response.status_code == 200

    def test_ranking_has_correct_fields(self):
        with patch('backend.main.get_db') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                (1, 'Warszawa', 7, 85)
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            response = client.get("/api/cities/ranking")
            data = response.json()
            city = data["ranking"][0]
            assert "name" in city
            assert "event_count" in city
            assert "avg_weather_score" in city

class TestEventsEndpoint:

    def test_events_returns_200(self):
        with patch('backend.main.get_db') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_db.return_value.cursor.return_value = mock_cursor
            response = client.get("/api/events")
            assert response.status_code == 200

    def test_events_filter_by_city(self):
        with patch('backend.main.get_db') as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_db.return_value.cursor.return_value = mock_cursor
            response = client.get("/api/events?city_id=1")
            assert response.status_code == 200
