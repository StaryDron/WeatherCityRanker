CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lat DECIMAL(9,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    radius INTEGER NOT NULL
);

CREATE TABLE city_forecasts (
    city_id INTEGER REFERENCES cities(id),
    dt INTEGER NOT NULL,
    dt_txt VARCHAR(20) NOT NULL,
    temp DECIMAL(5,2),
    feels_like DECIMAL(5,2),
    humidity INTEGER,
    pressure INTEGER,
    clouds_all INTEGER,
    wind_speed DECIMAL(5,2),
    weather_main VARCHAR(50),
    weather_description VARCHAR(100),
    PRIMARY KEY (city_id, dt)
);

CREATE TABLE events (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    local_date DATE NOT NULL,
    local_time TIME,
    dt INTEGER,
    city_id INTEGER NOT NULL,
    venue_name VARCHAR(255),
    category VARCHAR(100),
    url TEXT,
    weather_score INTEGER,
    is_recurring BOOLEAN DEFAULT FALSE,
    lat DECIMAL(9,6),
    lon DECIMAL(9,6),
    FOREIGN KEY (city_id, dt) REFERENCES city_forecasts(city_id, dt)
);

INSERT INTO cities (name, lat, lon, radius) VALUES
    ('Warszawa', 52.2297, 21.0122, 50),
    ('Krakow', 50.0647, 19.9450, 50),
    ('Wroclaw', 51.1079, 17.0385, 50),
    ('Gdansk', 54.3520, 18.6466, 50),
    ('Poznan', 52.4064, 16.9252, 50),
    ('Lodz', 51.7592, 19.4560, 50),
    ('Katowice', 50.2649, 19.0238, 50),
    ('Lublin', 51.2465, 22.5684, 50);
