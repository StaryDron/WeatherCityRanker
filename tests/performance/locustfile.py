from locust import HttpUser, task, between, TaskSet
from locust import events
import time

class EventsLoadTest(HttpUser):
    """Test obciazenia endpointu wydarzen"""
    wait_time = between(1, 2)
    weight = 3  # 3x czestszy niz ranking

    @task(4)
    def get_all_events(self):
        with self.client.get("/api/events", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "events" not in data:
                    response.failure("Brak klucza 'events' w odpowiedzi")
            else:
                response.failure(f"Blad HTTP: {response.status_code}")

    @task(3)
    def get_events_warszawa(self):
        with self.client.get("/api/events?city_id=1", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Blad HTTP: {response.status_code}")

    @task(2)
    def get_events_krakow(self):
        with self.client.get("/api/events?city_id=2", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Blad HTTP: {response.status_code}")

    @task(2)
    def get_events_filter_music(self):
        with self.client.get("/api/events?category=Music", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Blad HTTP: {response.status_code}")

    @task(1)
    def get_events_combined_filter(self):
        with self.client.get("/api/events?city_id=1&category=Music", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Blad HTTP: {response.status_code}")


class RankingLoadTest(HttpUser):
    """Test obciazenia endpointu rankingu"""
    wait_time = between(2, 4)
    weight = 1

    @task(3)
    def get_ranking(self):
        with self.client.get("/api/cities/ranking", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "ranking" not in data:
                    response.failure("Brak klucza 'ranking' w odpowiedzi")
                elif len(data["ranking"]) == 0:
                    response.failure("Pusta lista rankingu")
            else:
                response.failure(f"Blad HTTP: {response.status_code}")

    @task(1)
    def get_cities(self):
        with self.client.get("/api/cities", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Blad HTTP: {response.status_code}")
