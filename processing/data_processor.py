

import psycopg2
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.logger import get_logger
from dotenv import load_dotenv
from ingestion.openweather_client import OpenWeatherClient
from ingestion.ticketmaster_client import TicketMasterClient
from datetime import datetime, timezone, timedelta
import math

logger = get_logger("data_processor")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


class DataProcessor:
    def __init__(self):
        load_dotenv()
        self.conn = psycopg2.connect(
	    host=os.environ["POSTGRES_HOST"],
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ["POSTGRES_PORT"]
        )
        self.cursor = self.conn.cursor()
        self.weather_client = OpenWeatherClient()
        self.tm_client = TicketMasterClient()

    def get_cities(self):
        self.cursor.execute("SELECT id, name, lat, lon, radius FROM cities")
        return self.cursor.fetchall()

    def clear_data(self):
        logger.info("Czyszczenie bazy...")
        self.cursor.execute("DELETE FROM events")
        self.cursor.execute("DELETE FROM city_forecasts")
        self.conn.commit()

    def save_forecasts(self, city_id, forecast_data):
        forecasts = forecast_data.get("list", [])
        for item in forecasts:
            self.cursor.execute("""
                INSERT INTO city_forecasts 
                (city_id, dt, dt_txt, temp, feels_like, humidity, pressure, clouds_all, wind_speed, weather_main, weather_description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                city_id,
                item["dt"],
                item["dt_txt"],
                item["main"]["temp"],
                item["main"]["feels_like"],
                item["main"]["humidity"],
                item["main"]["pressure"],
                item["clouds"]["all"],
                item["wind"]["speed"],
                item["weather"][0]["main"],
                item["weather"][0]["description"]
            ))
        self.conn.commit()

    def find_forecast_dt(self, city_id, event_dt):
        self.cursor.execute("""
            SELECT dt FROM city_forecasts 
            WHERE city_id = %s AND dt <= %s
            ORDER BY dt DESC
            LIMIT 1
        """, (city_id, event_dt))
        row = self.cursor.fetchone()
        return row[0] if row else None
        
    
    def save_events(self, city_id, events_data, all_cities):
        events = events_data.get("_embedded", {}).get("events", [])
        saved = 0
        for event in events:
            try:
                venue = event.get("_embedded", {}).get("venues", [{}])[0]
                event_lat = venue.get("location", {}).get("latitude")
                event_lon = venue.get("location", {}).get("longitude")
    
                if event_lat and event_lon:
                    event_lat = float(event_lat)
                    event_lon = float(event_lon)
                    closest_city_id = min(
                        all_cities,
                        key=lambda c: haversine(event_lat, event_lon, float(c[2]), float(c[3]))
                    )[0]
                    if closest_city_id != city_id:
                        continue
    
                local_date = event["dates"]["start"]["localDate"]
                local_time = event["dates"]["start"].get("localTime")
                
                if local_time:
                    dt_str = f"{local_date}T{local_time}"
                else:
                    dt_str = f"{local_date}T15:00:00"
                    local_time = "15:00:00"
                event_dt = int(datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc).timestamp())
                
                forecast_dt = self.find_forecast_dt(city_id, event_dt)
                if forecast_dt is None:
                    continue
    
                category = event.get("classifications", [{}])[0].get("segment", {}).get("name", "Other")
    
                self.cursor.execute("""
                    INSERT INTO events (id, name, local_date, local_time, dt, city_id, venue_name, category, url, weather_score, is_recurring, lat, lon)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    event["id"],
                    event["name"],
                    local_date,
                    local_time,
                    forecast_dt,
                    city_id,
                    venue.get("name"),
                    category,
                    event.get("url"),
                    None,
                    False,
                    event_lat,
                    event_lon
                ))
                saved += 1
            except Exception as e:
                logger.error(f"Blad przy evencie {event.get('id')}: {e}")
                continue
        
        self.conn.commit()
        logger.info(f"Zapisano {saved} wydarzen dla miasta o id {city_id}.")

    def calculate_weather_score(self, category, weather_main, temp, wind_speed, humidity):
        weather_scores = {
            "Clear": 100,
            "Clouds": 75,
            "Drizzle": 50,
            "Rain": 30,
            "Thunderstorm": 10,
            "Snow": 20,
            "Mist": 60,
            "Fog": 50
        }
        score = weather_scores.get(weather_main, 60)
    
        indoor_categories = ["Music", "Arts & Theatre", "Film"]
        if category in indoor_categories:
            score = min(100, score + 20)
        
        outdoor_categories = ["Sports", "Miscellaneous"]
        if category in outdoor_categories:
            if temp < 5 or temp > 35:
                score -= 20
            if wind_speed > 10:
                score -= 15
            if humidity > 85:
                score -= 10
    
        return max(0, min(100, score))
    
    def update_weather_scores(self):
        self.cursor.execute("""
            SELECT e.id, e.category, e.city_id, e.dt,
                   cf.weather_main, cf.temp, cf.wind_speed, cf.humidity
            FROM events e
            JOIN city_forecasts cf ON e.city_id = cf.city_id AND e.dt = cf.dt
        """)
        events = self.cursor.fetchall()
        for event in events:
            event_id, category, city_id, dt, weather_main, temp, wind_speed, humidity = event
            score = self.calculate_weather_score(
                category, weather_main, float(temp), float(wind_speed), float(humidity)
            )
            self.cursor.execute(
                "UPDATE events SET weather_score = %s WHERE id = %s",
                (score, event_id)
            )
        self.conn.commit()

    def run(self):
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=5)
        start_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    
        self.clear_data()
        cities = self.get_cities()
        
        for city in cities:
            city_id, name, lat, lon, radius = city
    
            logger.info(f"Pobieranie prognoz i wydarzen dla miasta: {name}...")
            forecast = self.weather_client.get_forecast(lat=float(lat), lon=float(lon))
            if forecast:
                self.save_forecasts(city_id, forecast)
            
            events = self.tm_client.get_events(
                lat=float(lat),
                lon=float(lon),
                radius=radius,
                start_datetime=start_str,
                end_datetime=end_str
            )
            if events:
                self.save_events(city_id, events, cities)
        self.update_weather_scores()
        self.cursor.execute("""
            UPDATE events SET is_recurring = TRUE
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, COUNT(*) OVER (PARTITION BY name, venue_name, city_id) as cnt
                    FROM events
                ) sub WHERE cnt > 1
            )
        """)
        self.conn.commit()
        


if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()

    
