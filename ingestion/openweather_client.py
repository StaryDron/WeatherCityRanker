

import requests
import os
from dotenv import load_dotenv


class OpenWeatherClient:
    def __init__(self):
        self.url = "https://api.openweathermap.org/data/2.5/forecast?"
        load_dotenv()
        self.key = os.environ["OPENWEATHER_API_KEY"]
        self.units = "metric"
        self.cnt = 40
    
    def get_forecast(self, lat, lon):
         
        if lat is None or lon is None:
            print("nie podano lokalizacji")
            return None
            
        params = {
            "lat" : lat,
            "lon" : lon,
            "units" : self.units,
            "cnt" : self.cnt,
            "appid" : self.key
        }
            
        response = requests.get(self.url , params = params)

        if response.status_code != 200:
            print(f"Blad API: {response.status_code}")
            return None
        
        response_procesed = response.json()
        
        return response_procesed
        
