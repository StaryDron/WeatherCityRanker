

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="EventWeather PL", version="1.0.0")

def get_db():
    return psycopg2.connect(
        host= os.environ["POSTGRES_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=os.environ["POSTGRES_PORT"]
    )
# kom
@app.get("/api/cities")
def get_cities():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, lat, lon FROM cities ORDER BY name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"cities": [
        {"id": r[0], "name": r[1], "lat": float(r[2]), "lon": float(r[3])}
        for r in rows
    ]}

@app.get("/api/events")
def get_events(city_id: int = None, category: str = None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT e.id, e.name, e.local_date, e.local_time, e.city_id,
               e.venue_name, e.category, e.url, e.weather_score,
               e.is_recurring, e.lat, e.lon,
               cf.temp, cf.weather_main, cf.weather_description,
               cf.wind_speed, cf.humidity
        FROM events e
        JOIN city_forecasts cf ON e.city_id = cf.city_id AND e.dt = cf.dt
        WHERE 1=1
    """
    params = []
    if city_id:
        query += " AND e.city_id = %s"
        params.append(city_id)
    if category:
        query += " AND e.category = %s"
        params.append(category)
    query += " ORDER BY e.local_date, e.local_time"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"events": [
        {
            "id": r[0],
            "name": r[1],
            "local_date": str(r[2]),
            "local_time": str(r[3]) if r[3] else None,
            "city_id": r[4],
            "venue_name": r[5],
            "category": r[6],
            "url": r[7],
            "weather_score": r[8],
            "is_recurring": r[9],
            "lat": float(r[10]) if r[10] else None,
            "lon": float(r[11]) if r[11] else None,
            "temp": float(r[12]) if r[12] else None,
            "weather_main": r[13],
            "weather_description": r[14],
            "wind_speed": float(r[15]) if r[15] else None,
            "humidity": r[16]
        }
        for r in rows
    ]}

@app.get("/api/cities/ranking")
def get_ranking():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, COUNT(e.id) as event_count,
               ROUND(AVG(e.weather_score)) as avg_score
        FROM cities c
        LEFT JOIN events e ON c.id = e.city_id
        GROUP BY c.id, c.name
        ORDER BY event_count DESC, avg_score DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"ranking": [
        {"id": r[0], "name": r[1], "event_count": r[2], "avg_weather_score": float(r[3]) if r[3] else 0}
        for r in rows
    ]}

@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.name, e.local_date, e.local_time, e.city_id,
               e.venue_name, e.category, e.url, e.weather_score,
               e.is_recurring, e.lat, e.lon,
               cf.temp, cf.feels_like, cf.weather_main, cf.weather_description,
               cf.wind_speed, cf.humidity, cf.pressure, cf.clouds_all,
               c.name as city_name
        FROM events e
        JOIN city_forecasts cf ON e.city_id = cf.city_id AND e.dt = cf.dt
        JOIN cities c ON e.city_id = c.id
        WHERE e.id = %s
    """, (event_id,))
    r = cursor.fetchone()
    cursor.close()
    conn.close()
    if not r:
        return {"error": "Event not found"}
    return {
        "id": r[0], "name": r[1], "local_date": str(r[2]),
        "local_time": str(r[3]) if r[3] else None,
        "city_id": r[4], "city_name": r[20],
        "venue_name": r[5], "category": r[6], "url": r[7],
        "weather_score": r[8], "is_recurring": r[9],
        "lat": float(r[10]) if r[10] else None,
        "lon": float(r[11]) if r[11] else None,
        "forecast": {
            "temp": float(r[12]) if r[12] else None,
            "feels_like": float(r[13]) if r[13] else None,
            "weather_main": r[14], "weather_description": r[15],
            "wind_speed": float(r[16]) if r[16] else None,
            "humidity": r[17], "pressure": r[18], "clouds_all": r[19]
        }
    }
