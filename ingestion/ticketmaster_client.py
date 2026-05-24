import requests
import os
from dotenv import load_dotenv

class TicketMasterClient:
    def __init__(self):
        load_dotenv()
        self.url = "https://app.ticketmaster.com/discovery/v2/events.json"
        self.key = os.environ["TICKETMASTER_API_KEY"]
        self.country_code = "PL"

    def get_events(self, lat, lon, radius, start_datetime, end_datetime):
        params = {
            "apikey": self.key,
            "latlong": f"{lat},{lon}",
            "radius": radius,
            "unit": "km",
            "countryCode": self.country_code,
            "startDateTime": start_datetime,
            "endDateTime": end_datetime,
            "size": 200
        }
        response = requests.get(self.url, params=params)
        if response.status_code != 200:
            print(f"Blad API: {response.status_code}")
            return None
        return response.json()

