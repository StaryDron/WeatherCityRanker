const API = "http://localhost:8000";

let map;
let markers = [];
let overviewLoaded = false;

/* =========================
   POMOCNICZE FUNKCJE
========================= */

function weatherIcon(main) {
    const icons = {
        Clear: "☀️",
        Clouds: "☁️",
        Rain: "🌧️",
        Drizzle: "🌦️",
        Thunderstorm: "⛈️",
        Snow: "❄️",
        Mist: "🌫️",
        Fog: "🌫️"
    };

    return icons[main] || "🌤️";
}

function scoreClass(score) {
    const value = Number(score);

    if (value >= 75) return "score-high";
    if (value >= 50) return "score-mid";
    return "score-low";
}

function weatherStatusClass(score) {
    const value = Number(score);

    if (value >= 75) return "status-good";
    if (value >= 50) return "status-mid";
    return "status-bad";
}

function weatherLabel(score) {
    const value = Number(score);

    if (value >= 75) return "Idealna pogoda";
    if (value >= 50) return "Umiarkowana pogoda";
    return "Słaba pogoda";
}

function categoryLabel(category) {
    const labels = {
        Music: "Muzyka",
        Sports: "Sport",
        "Arts & Theatre": "Teatr i sztuka",
        Miscellaneous: "Inne"
    };

    return labels[category] || category || "Brak kategorii";
}

function escapeHTML(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function safeExternalUrl(url) {
    if (!url) return null;

    try {
        const parsedUrl = new URL(url);

        if (parsedUrl.protocol === "https:" || parsedUrl.protocol === "http:") {
            return escapeHTML(parsedUrl.href);
        }

        return null;
    } catch {
        return null;
    }
}

function formatScore(score) {
    const value = Number(score);

    if (Number.isNaN(value)) return "—";

    return Math.round(value);
}

async function fetchJSON(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Błąd API: ${response.status}`);
    }

    return response.json();
}

/* =========================
   NAVBAR
========================= */

function initializeNavbar() {
    const navbar = document.getElementById("mainNavbar");

    function updateNavbar() {
        if (window.scrollY > 30) {
            navbar.classList.add("scrolled");
        } else {
            navbar.classList.remove("scrolled");
        }
    }

    window.addEventListener("scroll", updateNavbar);
    updateNavbar();
}

/* =========================
   MAPA
========================= */

function initializeMap() {
    map = L.map("map").setView([52.0, 19.5], 6);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap"
    }).addTo(map);
}

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

function addMarker(event) {
    if (event.lat == null || event.lon == null) {
        return;
    }

    const icon = L.divIcon({
        className: "",
        html: `
            <div class="custom-map-marker">
                ${weatherIcon(event.weather_main)}
            </div>
        `,
        iconSize: [38, 38],
        iconAnchor: [19, 19],
        popupAnchor: [0, -19]
    });

    const marker = L.marker([event.lat, event.lon], { icon })
        .addTo(map)
        .bindPopup(`
            <div class="map-popup-title">
                ${escapeHTML(event.name)}
            </div>

            <div class="map-popup-info">
                📅 ${escapeHTML(event.local_date)}
                ${event.local_time ? escapeHTML(event.local_time.slice(0, 5)) : ""}
                <br>

                ${weatherIcon(event.weather_main)}
                ${escapeHTML(event.weather_main || "Brak danych")}
                · ${escapeHTML(event.temp ?? "—")}°C
                <br>

                Wynik pogody:
                <strong>${formatScore(event.weather_score)}/100</strong>
            </div>
        `);

    markers.push(marker);
}

function updateMapMarkers(events) {
    clearMarkers();

    events.forEach(addMarker);

    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.18));
    } else {
        map.setView([52.0, 19.5], 6);
    }
}

/* =========================
   MIASTA
========================= */

async function loadCities() {
    const select = document.getElementById("citySelect");

    try {
        const data = await fetchJSON(`${API}/api/cities`);
        const cities = data.cities || [];

        cities.forEach(city => {
            const option = document.createElement("option");
            option.value = city.id;
            option.textContent = city.name;
            select.appendChild(option);
        });

        document.getElementById("statCities").textContent = cities.length;
    } catch (error) {
        console.error("Nie udało się pobrać miast:", error);
        document.getElementById("statCities").textContent = "—";
    }
}

/* =========================
   RANKING
========================= */

function medalForPosition(position) {
    if (position === 0) return "🥇";
    if (position === 1) return "🥈";
    if (position === 2) return "🥉";
    return "📍";
}

async function loadRanking() {
    const container = document.getElementById("ranking");

    try {
        const data = await fetchJSON(`${API}/api/cities/ranking`);
        const ranking = data.ranking || [];

        if (ranking.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    Brak danych do wyświetlenia rankingu.
                </div>
            `;
            return;
        }

        document.getElementById("statBestCity").textContent = ranking[0].name;

        container.innerHTML = ranking.slice(0, 4).map((city, index) => {
            const score = formatScore(city.avg_weather_score);
            const width = Math.max(0, Math.min(100, Number(score) || 0));

            return `
                <div class="col-md-6 col-xl-3">
                    <article class="ranking-card ${index === 0 ? "first-place" : ""}">
                        <div class="ranking-position">0${index + 1}</div>

                        <div class="ranking-medal">
                            ${medalForPosition(index)}
                        </div>

                        <h3 class="ranking-city">
                            ${escapeHTML(city.name)}
                        </h3>

                        <div class="ranking-events">
                            ${escapeHTML(city.event_count)} wydarzeń
                        </div>

                        <div class="ranking-score-line">
                            <span>Średnia pogoda</span>
                            <span class="ranking-score-number ${scoreClass(score)}">
                                ${score}/100
                            </span>
                        </div>

                        <div class="ranking-track">
                            <div class="ranking-bar" style="width: ${width}%"></div>
                        </div>
                    </article>
                </div>
            `;
        }).join("");
    } catch (error) {
        console.error("Nie udało się pobrać rankingu:", error);

        container.innerHTML = `
            <div class="error-state">
                Nie udało się załadować rankingu miast.
            </div>
        `;
    }
}

/* =========================
   WYDARZENIA
========================= */

function createEventCard(event) {
    const ticketUrl = safeExternalUrl(event.url);
    const score = formatScore(event.weather_score);

    return `
        <div class="col-md-6 col-xl-4">
            <article class="event-card">

                <div class="event-top">
                    <span class="weather-status ${weatherStatusClass(score)}">
                        ${weatherIcon(event.weather_main)}
                        ${weatherLabel(score)}
                    </span>

                    <span class="event-score ${scoreClass(score)}">
                        ${score}/100
                    </span>
                </div>

                <h3 class="event-title">
                    ${escapeHTML(event.name)}
                </h3>

                ${
                    event.is_recurring
                        ? `<span class="recurring-badge">🔁 Wydarzenie cykliczne</span>`
                        : ""
                }

                <div class="event-details">
                    <div>
                        📅 ${escapeHTML(event.local_date)}
                        ${event.local_time ? `o ${escapeHTML(event.local_time.slice(0, 5))}` : ""}
                    </div>

                    <div>
                        📍 ${escapeHTML(event.venue_name || "Brak informacji o miejscu")}
                    </div>

                    <div>
                        🎭 ${escapeHTML(categoryLabel(event.category))}
                    </div>
                </div>

                <div class="weather-details">
                    <span class="weather-pill">
                        ${weatherIcon(event.weather_main)}
                        ${escapeHTML(event.weather_main || "—")}
                    </span>

                    <span class="weather-pill">
                        🌡️ ${escapeHTML(event.temp ?? "—")}°C
                    </span>

                    <span class="weather-pill">
                        💨 ${escapeHTML(event.wind_speed ?? "—")} m/s
                    </span>

                    <span class="weather-pill">
                        💧 ${escapeHTML(event.humidity ?? "—")}%
                    </span>
                </div>

                ${
                    ticketUrl
                        ? `
                            <a
                                href="${ticketUrl}"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="event-link"
                            >
                                Zobacz wydarzenie →
                            </a>
                        `
                        : ""
                }

            </article>
        </div>
    `;
}

function updateOverviewStatistics(events) {
    if (overviewLoaded) return;

    const goodWeatherEvents = events.filter(
        event => Number(event.weather_score) >= 75
    );

    document.getElementById("statEvents").textContent = events.length;
    document.getElementById("statGoodWeather").textContent = goodWeatherEvents.length;

    overviewLoaded = true;
}

async function loadEvents() {
    const eventsContainer = document.getElementById("events");
    const eventsCount = document.getElementById("eventsCount");

    const cityId = document.getElementById("citySelect").value;
    const category = document.getElementById("categorySelect").value;
    const goodWeatherOnly = document.getElementById("goodWeatherOnly").checked;

    const params = new URLSearchParams();

    if (cityId) {
        params.append("city_id", cityId);
    }

    if (category) {
        params.append("category", category);
    }

    eventsContainer.innerHTML = `
        <div class="loading-message">
            Ładowanie wydarzeń...
        </div>
    `;

    try {
        const query = params.toString();
        const url = query
            ? `${API}/api/events?${query}`
            : `${API}/api/events`;

        const data = await fetchJSON(url);
        const allEvents = data.events || [];

        updateOverviewStatistics(allEvents);

        const visibleEvents = goodWeatherOnly
            ? allEvents.filter(event => Number(event.weather_score) >= 75)
            : allEvents;

        eventsCount.textContent = visibleEvents.length;

        updateMapMarkers(visibleEvents);

        if (visibleEvents.length === 0) {
            eventsContainer.innerHTML = `
                <div class="empty-state">
                    Nie znaleziono wydarzeń spełniających wybrane kryteria.
                </div>
            `;
            return;
        }

        eventsContainer.innerHTML = visibleEvents
            .map(createEventCard)
            .join("");
    } catch (error) {
        console.error("Nie udało się pobrać wydarzeń:", error);

        eventsCount.textContent = "0";

        eventsContainer.innerHTML = `
            <div class="error-state">
                Nie udało się załadować wydarzeń.
                Sprawdź, czy backend działa na porcie 8000.
            </div>
        `;
    }
}

/* =========================
   FILTRY
========================= */

function initializeFilters() {
    document
        .getElementById("citySelect")
        .addEventListener("change", loadEvents);

    document
        .getElementById("categorySelect")
        .addEventListener("change", loadEvents);

    document
        .getElementById("goodWeatherOnly")
        .addEventListener("change", loadEvents);

    document
        .getElementById("clearFiltersBtn")
        .addEventListener("click", () => {
            document.getElementById("citySelect").value = "";
            document.getElementById("categorySelect").value = "";
            document.getElementById("goodWeatherOnly").checked = false;

            loadEvents();
        });
}

/* =========================
   START APLIKACJI
========================= */

document.addEventListener("DOMContentLoaded", async () => {
    initializeNavbar();
    initializeMap();
    initializeFilters();

    await Promise.all([
        loadCities(),
        loadRanking()
    ]);

    await loadEvents();
});
