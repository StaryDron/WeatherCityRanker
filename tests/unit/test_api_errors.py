import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import responses as responses_lib
import requests
from unittest.mock import patch, MagicMock
from ingestion.openweather_client import OpenWeatherClient
from ingestion.ticketmaster_client import TicketMasterClient

class TestOpenWeatherClientErrors:

    def setup_method(self):
        with patch.dict(os.environ, {'OPENWEATHER_API_KEY': 'test_key'}):
            self.client = OpenWeatherClient()

    @responses_lib.activate
    def test_returns_none_on_404(self):
        responses_lib.add(
            responses_lib.GET,
            "https://api.openweathermap.org/data/2.5/forecast",
            json={"message": "city not found"},
            status=404
        )
        result = self.client.get_forecast(lat=0, lon=0)
        assert result is None

    @responses_lib.activate
    def test_returns_none_on_401(self):
        responses_lib.add(
            responses_lib.GET,
            "https://api.openweathermap.org/data/2.5/forecast",
            json={"message": "Invalid API key"},
            status=401
        )
        result = self.client.get_forecast(lat=52.23, lon=21.01)
        assert result is None

class TestTicketMasterClientErrors:

    def setup_method(self):
        with patch.dict(os.environ, {'TICKETMASTER_API_KEY': 'test_key'}):
            self.client = TicketMasterClient()

    @responses_lib.activate
    def test_returns_none_on_error(self):
        responses_lib.add(
            responses_lib.GET,
            "https://app.ticketmaster.com/discovery/v2/events.json",
            json={"error": "service unavailable"},
            status=503
        )
        result = self.client.get_events(
            lat=52.23, lon=21.01, radius=50,
            start_datetime="2026-01-01T00:00:00Z",
            end_datetime="2026-01-06T00:00:00Z"
        )
        assert result is None

    @responses_lib.activate
    def test_empty_response_handled(self):
        responses_lib.add(
            responses_lib.GET,
            "https://app.ticketmaster.com/discovery/v2/events.json",
            json={"page": {"totalElements": 0}},
            status=200
        )
        result = self.client.get_events(
            lat=52.23, lon=21.01, radius=50,
            start_datetime="2026-01-01T00:00:00Z",
            end_datetime="2026-01-06T00:00:00Z"
        )
        assert result is not None
