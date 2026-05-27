import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.data_processor import DataProcessor
from unittest.mock import patch, MagicMock

@patch('processing.data_processor.psycopg2.connect')
@patch('processing.data_processor.OpenWeatherClient')
@patch('processing.data_processor.TicketMasterClient')
def get_processor(mock_tm, mock_ow, mock_db):
    return DataProcessor()

class TestWeatherScore:

    def setup_method(self):
        with patch('processing.data_processor.psycopg2.connect'), \
             patch('processing.data_processor.OpenWeatherClient'), \
             patch('processing.data_processor.TicketMasterClient'):
            self.processor = DataProcessor()

    def test_clear_sky_music_event(self):
        score = self.processor.calculate_weather_score("Music", "Clear", 20, 3, 50)
        assert score == 100

    def test_rain_outdoor_sport(self):
        score = self.processor.calculate_weather_score("Sports", "Rain", 15, 5, 70)
        assert score < 50

    def test_score_never_below_zero(self):
        score = self.processor.calculate_weather_score("Sports", "Thunderstorm", 0, 20, 95)
        assert score >= 0

    def test_score_never_above_100(self):
        score = self.processor.calculate_weather_score("Music", "Clear", 22, 2, 40)
        assert score <= 100

    def test_indoor_event_ignores_bad_weather(self):
        indoor = self.processor.calculate_weather_score("Arts & Theatre", "Rain", 15, 5, 80)
        outdoor = self.processor.calculate_weather_score("Sports", "Rain", 15, 5, 80)
        assert indoor > outdoor

    def test_extreme_cold_reduces_outdoor_score(self):
        cold = self.processor.calculate_weather_score("Sports", "Clear", 2, 3, 50)
        warm = self.processor.calculate_weather_score("Sports", "Clear", 20, 3, 50)
        assert cold < warm
