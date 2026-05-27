# WeatherCityRanker

Aplikacja agregująca wydarzenia kulturalne i sportowe w polskich miastach z prognozą pogody na dzień każdego wydarzenia. System automatycznie ocenia każde wydarzenie wskaźnikiem `weather_score` (0-100), pomagając użytkownikom wybrać najlepszy termin wyjścia z domu.

## Funkcjonalności

- Przegląd nadchodzących wydarzeń w 8 polskich miastach (Warszawa, Kraków, Wrocław, Gdańsk, Poznań, Łódź, Katowice, Lublin)
- Prognoza pogody na dzień każdego wydarzenia
- Ocena weather_score uwzględniająca kategorię wydarzenia (indoor/outdoor) i warunki atmosferyczne
- Filtrowanie wydarzeń po mieście, kategorii i jakości pogody
- Interaktywna mapa wydarzeń (Leaflet.js)
- Ranking miast według liczby wydarzeń i średniego weather_score
- Automatyczna aktualizacja danych co 24 godziny

## Architektura systemu

System zbudowany w architekturze warstwowej pipeline'u danych:

### Źródła danych

- **Ticketmaster Discovery API** — wydarzenia kulturalne i sportowe w Polsce (koncerty, teatr, sport). Filtrowanie po współrzędnych geograficznych i promieniu 50km dla każdego miasta.
- **OpenWeatherMap Forecast API** — prognoza pogody 5-dniowa (40 pomiarów co 3h). Parametry: temperatura, odczuwalna, wilgotność, ciśnienie, zachmurzenie, prędkość wiatru, opis pogody.

### Komponenty

| Komponent | Technologia | Odpowiedzialność |
|-----------|-------------|------------------|
| Ingestion Service | Python, APScheduler | Pobieranie danych z API co 24h |
| Processing Module | Python | Normalizacja, łączenie danych, obliczanie weather_score |
| Baza danych | PostgreSQL 16 | Trwałe przechowywanie wydarzeń i prognoz |
| Backend API | Python, FastAPI | REST API z automatyczną dokumentacją Swagger |
| Frontend | HTML, Bootstrap 5, Leaflet.js | Interfejs użytkownika z mapą i filtrami |

### Schemat bazy danych

cities (id, name, lat, lon, radius)
│
└── city_forecasts (city_id, dt, temp, feels_like, humidity,
│                   pressure, clouds_all, wind_speed,
│                   weather_main, weather_description)
│
└── events (id, name, local_date, local_time, dt, city_id,
venue_name, category, url, weather_score,
is_recurring, lat, lon)
│
└── FK(city_id, dt) → city_forecasts

## Uzasadnienie wyboru technologii

| Technologia | Uzasadnienie |
|-------------|--------------|
| Python 3.12 | Bogaty ekosystem bibliotek do integracji API i przetwarzania danych |
| FastAPI | Automatyczna generacja dokumentacji Swagger, wysoka wydajność, natywna walidacja przez Pydantic |
| PostgreSQL 16 | Relacyjna baza z obsługą kluczy kompozytowych, niezbędnych do łączenia wydarzeń z prognozami |
| APScheduler | Lekki scheduler bez zewnętrznych zależności, wystarczający dla interwału 24h |
| Docker + Compose | Izolacja środowisk, powtarzalne uruchomienie na dowolnym hoście |
| Bootstrap 5 | Szybki development responsywnego UI bez pisania CSS od zera |
| Leaflet.js | Lekka biblioteka map open-source, nie wymaga klucza API jak Google Maps |

## Struktura projektu

WeatherCityRanker/
├── backend/               # FastAPI REST API
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── ingestion/             # Pobieranie danych z API
│   ├── Dockerfile
│   ├── openweather_client.py
│   ├── ticketmaster_client.py
│   ├── scheduler.py
│   └── logger.py
├── processing/            # Przetwarzanie i zapis do bazy
│   └── data_processor.py
├── frontend/              # Interfejs użytkownika
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
├── db/
│   └── init.sql           # Schemat bazy danych
├── tests/
│   ├── unit/              # Testy jednostkowe (pytest)
│   └── performance/       # Testy wydajnościowe (locust)
├── docs/
│   └── architecture/      # Diagramy C4 i UML (.mmd)
├── docker-compose.yml          # Środowisko produkcyjne
├── docker-compose.dev.yml      # Środowisko deweloperskie
├── docker-compose.test.yml     # Środowisko testowe
└── .env.example               # Szablon zmiennych środowiskowych

## Uruchomienie

### Wymagania

- Docker
- Docker Compose
- Klucze API: [OpenWeatherMap](https://openweathermap.org/api) i [Ticketmaster](https://developer.ticketmaster.com)

### Krok po kroku

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/StaryDron/WeatherCityRanker.git
cd WeatherCityRanker

# 2. Utwórz plik .env na podstawie szablonu
cp .env.example .env
# Uzupełnij .env swoimi kluczami API i hasłem do bazy

# 3. Uruchom wszystkie kontenery
docker-compose up -d

# 4. Sprawdź status kontenerów
docker-compose ps
```

Aplikacja dostępna pod adresem: `http://localhost:8090`
API i dokumentacja Swagger: `http://localhost:8000/docs`

### Środowiska

```bash
# Deweloperskie (hot-reload, baza dostępna z hosta na porcie 5433)
docker-compose -f docker-compose.dev.yml up -d

# Testowe (uruchamia pytest i locust automatycznie)
docker-compose -f docker-compose.test.yml up

# Produkcyjne
docker-compose up -d
```

## Testy

### Testy jednostkowe

```bash
source venv/bin/activate
pytest tests/unit -v
```

Pokrycie testów:
- `test_weather_score.py` — logika obliczania weather_score
- `test_haversine.py` — algorytm przypisywania wydarzeń do miast
- `test_api_endpoints.py` — endpointy REST API
- `test_api_errors.py` — obsługa błędów zewnętrznych API

### Testy wydajnościowe (Locust)

```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 30s
```

Wyniki testów obciążeniowych:

| Użytkownicy | Śr. czas odpowiedzi | Błędy |
|-------------|---------------------|-------|
| 10          | 29ms                | 0%    |
| 50          | 78ms                | 0%    |
| 100         | 903ms               | 0%    |

## API Endpoints

Pełna dokumentacja dostępna pod `/docs` (Swagger UI).

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/api/cities` | Lista obsługiwanych miast |
| GET | `/api/events` | Lista wydarzeń (filtry: city_id, category) |
| GET | `/api/events/{id}` | Szczegóły wydarzenia z prognozą |
| GET | `/api/cities/ranking` | Ranking miast według wydarzeń i pogody |

## Logowanie

Logi zapisywane do `logs/app.log` oraz wyświetlane na konsoli.
Poziom logowania: `DEBUG` w środowisku dev, `INFO` w produkcji.

