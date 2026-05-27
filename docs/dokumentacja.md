# Dokumentacja projektu — EventWeather PL

## 1. Cel projektu

**EventWeather PL** to aplikacja webowa umożliwiająca przeglądanie wydarzeń w polskich miastach razem z prognozowaną pogodą. System łączy dane o wydarzeniach z danymi meteorologicznymi, a następnie wyznacza dla wydarzeń wynik `weather_score` w skali od 0 do 100.

Główny cel systemu:

> Ułatwienie użytkownikowi wyboru wydarzenia na podstawie miejsca, kategorii i warunków pogodowych.

Projekt realizuje pełny przepływ danych:

```text
zewnętrzne API -> pobieranie danych -> przetwarzanie -> PostgreSQL -> REST API -> frontend WWW
```

## 2. Zakres funkcjonalny

System umożliwia:

- pobieranie wydarzeń odbywających się w Polsce;
- pobieranie pięciodniowej prognozy pogody dla obsługiwanych miast;
- łączenie wydarzenia z odpowiadającą mu prognozą;
- obliczanie wskaźnika `weather_score`;
- przeglądanie wydarzeń w aplikacji webowej;
- filtrowanie wydarzeń po mieście i kategorii;
- filtrowanie wydarzeń o dobrej pogodzie;
- wyświetlanie wydarzeń na mapie;
- prezentację rankingu miast;
- korzystanie z REST API oraz dokumentacji Swagger.

System inicjalnie obsługuje osiem miast:

| Miasto | Promień wyszukiwania wydarzeń |
|---|---:|
| Warszawa | 50 km |
| Kraków | 50 km |
| Wrocław | 50 km |
| Gdańsk | 50 km |
| Poznań | 50 km |
| Łódź | 50 km |
| Katowice | 50 km |
| Lublin | 50 km |

## 3. Źródła danych

### 3.1. Ticketmaster Discovery API

Moduł `ingestion/ticketmaster_client.py` komunikuje się z API Ticketmaster:

```text
GET https://app.ticketmaster.com/discovery/v2/events.json
```

API dostarcza informacje o wydarzeniach:

- identyfikator i nazwa wydarzenia;
- data oraz godzina rozpoczęcia;
- miejsce wydarzenia;
- kategoria;
- adres URL;
- współrzędne geograficzne.

Zapytania są ograniczone do Polski przez parametr:

```text
countryCode=PL
```

Wydarzenia są pobierane dla lokalizacji każdego miasta w promieniu zapisanym w bazie danych.

### 3.2. OpenWeatherMap Forecast API

Moduł `ingestion/openweather_client.py` komunikuje się z API OpenWeatherMap:

```text
GET https://api.openweathermap.org/data/2.5/forecast
```

API dostarcza prognozę pogody na podstawie współrzędnych miasta. System pobiera maksymalnie 40 punktów prognozy w jednostkach metrycznych:

```text
units=metric
cnt=40
```

Zapisywane są następujące dane:

- temperatura;
- temperatura odczuwalna;
- wilgotność;
- ciśnienie;
- zachmurzenie;
- prędkość wiatru;
- typ i opis pogody.

## 4. Architektura systemu

System został zaprojektowany w architekturze warstwowej. Poszczególne komponenty mają rozdzielone odpowiedzialności.

| Warstwa | Komponent | Odpowiedzialność |
|---|---|---|
| Akwizycja danych | `ingestion/` | Pobieranie danych z Ticketmaster i OpenWeatherMap oraz harmonogram aktualizacji. |
| Przetwarzanie danych | `processing/data_processor.py` | Integracja danych, przypisanie wydarzeń do miast i obliczanie `weather_score`. |
| Baza danych | `db/init.sql`, PostgreSQL | Trwałe przechowywanie miast, prognoz i wydarzeń. |
| Backend | `backend/main.py`, FastAPI | Udostępnienie danych przez REST API. |
| Frontend | `frontend/`, Nginx | Prezentacja danych użytkownikowi. |
| Środowisko | Docker Compose | Uruchomienie komponentów w kontenerach. |

### 4.1. Diagramy

Diagramy architektury znajdują się w katalogu:

```text
docs/architecture/
├── context_diagram.png
├── container_diagram.png
├── deployment_diagrma.png
└── uml_component.png
```

| Diagram | Zakres |
|---|---|
| `context_diagram.png` | Użytkownik, system oraz dwa zewnętrzne API. |
| `container_diagram.png` | Frontend, backend, ingestion + processing oraz baza danych. |
| `deployment_diagrma.png` | Kontenery i środowiska uruchomieniowe. |
| `uml_component.png` | Komponenty kodu oraz zależności pomiędzy nimi. |

**Ważne:** `processing` jest modułem kodu używanym przez usługę `ingestion`, a nie osobnym kontenerem Docker.

## 5. Przepływ danych

Aktualizacja danych przebiega następująco:

1. Kontener `ingestion` uruchamia skrypt `ingestion/scheduler.py`.
2. Scheduler wykonuje zadanie aktualizacji natychmiast po starcie oraz później cyklicznie.
3. Klasa `DataProcessor` pobiera listę miast z tabeli `cities`.
4. Dla każdego miasta klient `OpenWeatherClient` pobiera prognozę pogody.
5. Prognozy zapisywane są do tabeli `city_forecasts`.
6. Dla każdego miasta klient `TicketMasterClient` pobiera wydarzenia.
7. Wydarzenie jest przypisywane do najbliższego miasta na podstawie odległości Haversine'a.
8. System dopasowuje wydarzeniu punkt prognozy.
9. Wydarzenie zapisywane jest do tabeli `events`.
10. Dla wydarzeń obliczany jest `weather_score`.
11. Backend odczytuje zapisane dane i udostępnia je frontendowi jako JSON.

Schemat przepływu:

```text
Ticketmaster Discovery API --------┐
                                   ├--> Ingestion + Processing --> PostgreSQL
OpenWeatherMap Forecast API -------┘                                |
                                                                     v
Użytkownik <-- Frontend WWW <-- REST / JSON <-- Backend FastAPI -----┘
```

## 6. Harmonogram pobierania danych

Za cykliczne odświeżanie danych odpowiada plik:

```text
ingestion/scheduler.py
```

Po uruchomieniu kontenera aktualizacja zostaje wykonana od razu. Następnie scheduler powtarza zadanie co określoną liczbę godzin.

Interwał ustawia się w pliku `.env`:

```env
INGESTION_INTERVAL_HOURS=6
```

W przypadku braku tej zmiennej kod wykorzystuje domyślną wartość `24` godzin.

## 7. Przetwarzanie danych

### 7.1. Przypisanie wydarzenia do miasta

Dane Ticketmaster mogą zwrócić wydarzenie znajdujące się w zasięgu więcej niż jednego miasta. System oblicza odległość wydarzenia od wszystkich obsługiwanych miast przy użyciu funkcji Haversine'a, a następnie przypisuje wydarzenie tylko do miasta znajdującego się najbliżej.

### 7.2. Dopasowanie prognozy

Wydarzenie jest łączone z prognozą na podstawie miasta i czasu. System wybiera ostatni zapisany punkt prognozy niepóźniejszy niż czas wydarzenia:

```sql
SELECT dt
FROM city_forecasts
WHERE city_id = %s
  AND dt <= %s
ORDER BY dt DESC
LIMIT 1;
```

Jeżeli nie istnieje pasująca prognoza, wydarzenie nie jest zapisywane.

### 7.3. Ocena warunków pogodowych

Wskaźnik `weather_score` określa warunki pogodowe dla wydarzenia w skali `0–100`.

| Rodzaj pogody | Wynik bazowy |
|---|---:|
| `Clear` | 100 |
| `Clouds` | 75 |
| `Mist` | 60 |
| Inna wartość | 60 |
| `Drizzle` | 50 |
| `Fog` | 50 |
| `Rain` | 30 |
| `Snow` | 20 |
| `Thunderstorm` | 10 |

Reguły modyfikujące wynik:

| Warunek | Modyfikacja |
|---|---:|
| Kategoria `Music`, `Arts & Theatre` lub `Film` | `+20`, maksymalnie do 100 |
| Kategoria `Sports` lub `Miscellaneous` oraz temperatura poniżej 5°C albo powyżej 35°C | `-20` |
| Kategoria `Sports` lub `Miscellaneous` oraz wiatr powyżej 10 m/s | `-15` |
| Kategoria `Sports` lub `Miscellaneous` oraz wilgotność powyżej 85% | `-10` |

Wynik końcowy jest ograniczany do przedziału `0–100`.

## 8. Baza danych

Baza danych działa na obrazie Docker:

```text
postgres:16-alpine
```

Schemat tworzony jest przez plik:

```text
db/init.sql
```

### 8.1. Tabela `cities`

| Kolumna | Typ | Ograniczenia | Znaczenie |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Identyfikator miasta. |
| `name` | `VARCHAR(100)` | `NOT NULL` | Nazwa miasta. |
| `lat` | `DECIMAL(9,6)` | `NOT NULL` | Szerokość geograficzna. |
| `lon` | `DECIMAL(9,6)` | `NOT NULL` | Długość geograficzna. |
| `radius` | `INTEGER` | `NOT NULL` | Promień wyszukiwania wydarzeń w km. |

### 8.2. Tabela `city_forecasts`

| Kolumna | Typ | Ograniczenia | Znaczenie |
|---|---|---|---|
| `city_id` | `INTEGER` | `REFERENCES cities(id)` | Powiązanie z miastem. |
| `dt` | `INTEGER` | część `PRIMARY KEY` | Czas prognozy jako Unix timestamp. |
| `dt_txt` | `VARCHAR(20)` | `NOT NULL` | Czytelna data i czas prognozy. |
| `temp` | `DECIMAL(5,2)` |  | Temperatura. |
| `feels_like` | `DECIMAL(5,2)` |  | Temperatura odczuwalna. |
| `humidity` | `INTEGER` |  | Wilgotność. |
| `pressure` | `INTEGER` |  | Ciśnienie. |
| `clouds_all` | `INTEGER` |  | Zachmurzenie. |
| `wind_speed` | `DECIMAL(5,2)` |  | Prędkość wiatru. |
| `weather_main` | `VARCHAR(50)` |  | Główny typ pogody. |
| `weather_description` | `VARCHAR(100)` |  | Opis pogody. |

Klucz główny:

```sql
PRIMARY KEY (city_id, dt)
```

### 8.3. Tabela `events`

| Kolumna | Typ | Ograniczenia | Znaczenie |
|---|---|---|---|
| `id` | `VARCHAR(50)` | `PRIMARY KEY` | Identyfikator wydarzenia Ticketmaster. |
| `name` | `VARCHAR(255)` | `NOT NULL` | Nazwa wydarzenia. |
| `local_date` | `DATE` | `NOT NULL` | Data wydarzenia. |
| `local_time` | `TIME` |  | Godzina wydarzenia. |
| `dt` | `INTEGER` | część klucza obcego | Czas przypisanej prognozy. |
| `city_id` | `INTEGER` | `NOT NULL`, część klucza obcego | Miasto wydarzenia. |
| `venue_name` | `VARCHAR(255)` |  | Miejsce wydarzenia. |
| `category` | `VARCHAR(100)` |  | Kategoria wydarzenia. |
| `url` | `TEXT` |  | Link zewnętrzny do wydarzenia. |
| `weather_score` | `INTEGER` |  | Ocena warunków pogodowych. |
| `is_recurring` | `BOOLEAN` | `DEFAULT FALSE` | Informacja o powtarzalności. |
| `lat` | `DECIMAL(9,6)` |  | Szerokość geograficzna wydarzenia. |
| `lon` | `DECIMAL(9,6)` |  | Długość geograficzna wydarzenia. |

Relacje:

```text
city_forecasts.city_id -> cities.id
events.(city_id, dt) -> city_forecasts.(city_id, dt)
```

## 9. Backend API

Backend znajduje się w pliku:

```text
backend/main.py
```

Został zaimplementowany z wykorzystaniem FastAPI. Dane pobiera bezpośrednio z PostgreSQL za pomocą biblioteki `psycopg2`.

Po uruchomieniu backendu automatyczna dokumentacja Swagger jest dostępna pod adresem:

```text
http://localhost:8000/docs
```

### 9.1. Endpointy

| Metoda | Endpoint | Opis | Parametry |
|---|---|---|---|
| `GET` | `/api/cities` | Zwraca listę obsługiwanych miast. | brak |
| `GET` | `/api/events` | Zwraca wydarzenia z pogodą i oceną. | `city_id`, `category` |
| `GET` | `/api/events/{event_id}` | Zwraca szczegóły jednego wydarzenia. | identyfikator w ścieżce |
| `GET` | `/api/cities/ranking` | Zwraca ranking miast. | brak |

### 9.2. Przykładowe wywołania

```bash
curl http://localhost:8000/api/cities
curl http://localhost:8000/api/events
curl "http://localhost:8000/api/events?city_id=1"
curl "http://localhost:8000/api/events?category=Music"
curl http://localhost:8000/api/cities/ranking
```

### 9.3. Przykładowa odpowiedź `/api/events`

```json
{
  "events": [
    {
      "id": "event_id",
      "name": "Nazwa wydarzenia",
      "local_date": "2026-05-30",
      "local_time": "19:00:00",
      "city_id": 1,
      "venue_name": "Nazwa miejsca",
      "category": "Music",
      "weather_score": 95,
      "temp": 20.5,
      "weather_main": "Clear",
      "weather_description": "clear sky",
      "wind_speed": 3.1,
      "humidity": 52
    }
  ]
}
```

## 10. Frontend

Frontend znajduje się w katalogu:

```text
frontend/
```

Aplikacja frontendowa komunikuje się z backendem przez adres zapisany w `frontend/js/app.js`:

```javascript
const API = "http://localhost:8000";
```

Frontend realizuje:

- ładowanie miast;
- ładowanie listy wydarzeń;
- pobieranie rankingu miast;
- obsługę filtrów;
- wyświetlanie wyniku pogodowego;
- tworzenie markerów na mapie Leaflet;
- prezentację komunikatów błędów.

Za serwowanie plików statycznych w Dockerze odpowiada Nginx.

## 11. Logowanie i błędy

### 11.1. Logowanie

Konfiguracja logowania znajduje się w pliku:

```text
ingestion/logger.py
```

Logi zapisywane są:

- w konsoli kontenera;
- w pliku `logs/app.log`.

Poziom logowania:

| Wartość `APP_ENV` | Poziom logów |
|---|---|
| `dev` | `DEBUG` |
| inna wartość | `INFO` |

Logger jest używany w:

- `ingestion/scheduler.py`;
- `processing/data_processor.py`.

### 11.2. Obsługa błędów

W aplikacji zaimplementowano podstawową obsługę błędów:

- nieudane wywołanie zewnętrznego API powoduje zwrócenie `None` i pominięcie zapisu danych;
- błąd pojedynczego wydarzenia jest logowany, ale nie przerywa przetwarzania pozostałych wydarzeń;
- błąd całej aktualizacji jest przechwytywany przez scheduler i rejestrowany w logach;
- frontend wyświetla komunikat, gdy backend jest niedostępny lub nie zwraca danych.

## 12. Konfiguracja środowiska

Na podstawie pliku `.env.example` należy utworzyć plik `.env`:

```bash
cp .env.example .env
```

Przykładowa konfiguracja:

```env
OPENWEATHER_API_KEY=twoj_klucz_tutaj
TICKETMASTER_API_KEY=twoj_klucz_tutaj

POSTGRES_USER=weatherapp
POSTGRES_PASSWORD=zmien_na_silne_haslo
POSTGRES_DB=weatherapp_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
APP_ENV=dev
INGESTION_INTERVAL_HOURS=6
```

Klucze API i hasła nie powinny być umieszczane w publicznym repozytorium.

## 13. Uruchomienie systemu

### 13.1. Środowisko demonstracyjne

```bash
docker-compose -f docker-compose.yml up --build -d
```

| Element | Adres |
|---|---|
| Frontend | `http://localhost:8090` |
| Backend API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |

Podgląd uruchomionych kontenerów:

```bash
docker ps
```

Podgląd logów pobierania danych:

```bash
docker logs weatherapp_ingestion --tail 100
```

Zatrzymanie środowiska:

```bash
docker-compose -f docker-compose.yml down
```

### 13.2. Środowisko developerskie

```bash
docker-compose -f docker-compose.dev.yml up --build
```

| Usługa | Port hosta | Port kontenera |
|---|---:|---:|
| Frontend DEV | 8090 | 80 |
| Backend DEV | 8001 | 8000 |
| PostgreSQL DEV | 5433 | 5432 |

Backend developerski uruchamiany jest z opcją automatycznego przeładowania kodu:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Do poprawy:** frontend odwołuje się obecnie do `http://localhost:8000`, a backend DEV jest wystawiony na hoście na porcie `8001`. Przed demonstracją środowiska DEV konfigurację trzeba ujednolicić.

### 13.3. Środowisko testowe

```bash
docker-compose -f docker-compose.test.yml up --build
```

Środowisko testowe zawiera:

- `weatherapp_db_test` — izolowaną bazę PostgreSQL;
- `weatherapp_backend_test` — kontener wykonujący testy Pytest;
- `weatherapp_locust` — kontener przeznaczony do testów wydajnościowych.

## 14. Testy

Zgodnie z wymaganiami projektu należy przedstawić testy jednostkowe oraz podstawowe testy wydajnościowe.

### 14.1. Testy jednostkowe

Testy jednostkowe powinny obejmować:

| Testowany element | Cel testu |
|---|---|
| `calculate_weather_score()` | sprawdzenie reguł oceny pogody i zakresu 0–100 |
| `haversine()` | sprawdzenie poprawności obliczeń odległości |
| endpointy API | sprawdzenie formatu i działania odpowiedzi |
| obsługa błędów API | sprawdzenie zachowania przy błędzie źródła zewnętrznego |

Uruchomienie:

```bash
pytest tests/unit -v --cov=. --cov-report=term-missing
```

### 14.2. Testy wydajnościowe

Do testów wydajnościowych wykorzystywany jest Locust. Scenariusz powinien symulować użytkowników pobierających listę wydarzeń, miasta i ranking.

Uruchomienie lokalne przeciwko działającemu backendowi:

```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

Panel Locust:

```text
http://localhost:8089
```

Tabela wyników do uzupełnienia po wykonaniu pomiarów:

| Użytkownicy | Żądania | Błędy | Średni czas | Mediana | Maksymalny czas |
|---:|---:|---:|---:|---:|---:|
| 10 | 158 | 0 | 29,47 ms | 26 ms | 70,46 ms |
| 50 | 702 | 0 | 79,43 ms | 55 ms | 453,22 ms |
| 100 | 948 | 0 | 900,39 ms | 1000 ms | 1794,82 ms |

## 15. Uzasadnienie wyboru technologii

| Technologia | Zastosowanie | Uzasadnienie |
|---|---|---|
| Python | ingestion, processing, backend | Umożliwia szybką implementację integracji API i logiki biznesowej. |
| FastAPI | backend REST API | Automatycznie generuje Swagger/OpenAPI i pozwala łatwo tworzyć endpointy. |
| Uvicorn | uruchomienie backendu | Lekki serwer ASGI współpracujący z FastAPI. |
| PostgreSQL 16 | baza danych | Relacyjny model odpowiada związkom między miastami, prognozami i wydarzeniami. |
| requests | klienci API | Prosta obsługa żądań HTTP w Pythonie. |
| APScheduler | harmonogram | Umożliwia cykliczne odświeżanie danych. |
| JavaScript | logika frontendu | Umożliwia dynamiczne filtrowanie i pobieranie danych z API. |
| Leaflet | mapa | Lekka biblioteka do interaktywnej wizualizacji lokalizacji. |
| Nginx | frontend | Wydajne serwowanie statycznych plików strony. |
| Docker Compose | środowisko | Powtarzalne uruchamianie wielu zależnych usług. |
| Pytest | testy jednostkowe | Standardowe narzędzie do testowania aplikacji Python. |
| Locust | testy wydajnościowe | Umożliwia symulowanie ruchu użytkowników. |

## 16. Ograniczenia i dalszy rozwój

Obecna wersja systemu jest prototypem demonstracyjnym. Najważniejsze ograniczenia:

- przy synchronizacji stare prognozy i wydarzenia są usuwane, więc aplikacja nie zachowuje historii;
- `weather_score` jest obliczany regułowo i nie uwzględnia wszystkich czynników pogodowych;
- frontend posiada stały adres API, który trzeba dostosować do środowiska DEV;
- system nie zawiera logowania użytkowników ani zapisywania ulubionych wydarzeń.

Możliwy dalszy rozwój:

- przechowywanie historii i analiz zmian w czasie;
- obsługa większej liczby miast;
- cache dla endpointów API;
- automatyczne testy CI/CD;
- monitoring aplikacji;
- konto użytkownika i lista ulubionych wydarzeń;
- rozwinięcie algorytmu `weather_score`.