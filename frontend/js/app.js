const API = "http://localhost:8000";

function weatherIcon(main) {
    const icons = {
        "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️",
        "Drizzle": "🌦️", "Thunderstorm": "⛈️", "Snow": "❄️",
        "Mist": "🌫️", "Fog": "🌫️"
    };
    return icons[main] || "🌡️";
}

function scoreClass(score) {
    if (score >= 75) return "score-high";
    if (score >= 50) return "score-mid";
    return "score-low";
}

const map = L.map("map").setView([52.0, 19.5], 6);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap"
}).addTo(map);
let markers = [];

function clearMarkers() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
}

function addMarker(event) {
    if (!event.lat || !event.lon) return;
    const marker = L.marker([event.lat, event.lon])
        .addTo(map)
        .bindPopup(`
            <b>${event.name}</b><br>
            ${event.local_date} ${event.local_time || ""}<br>
            ${weatherIcon(event.weather_main)} ${event.temp}°C<br>
            Score: ${event.weather_score}/100
        `);
    markers.push(marker);
}

async function loadCities() {
    const res = await fetch(`${API}/api/cities`);
    const data = await res.json();
    const select = document.getElementById("citySelect");
    data.cities.forEach(city => {
        const opt = document.createElement("option");
        opt.value = city.id;
        opt.textContent = city.name;
        select.appendChild(opt);
    });
}

async function loadRanking() {
    const res = await fetch(`${API}/api/cities/ranking`);
    const data = await res.json();
    const max = data.ranking[0]?.event_count || 1;
    const html = data.ranking.map(city => `
        <div class="col-md-3 col-6 mb-3">
            <div class="card p-3">
                <div class="fw-bold">${city.name}</div>
                <div class="text-muted small">${city.event_count} wydarzeń</div>
                <div class="ranking-bar mt-2" style="width:${(city.event_count/max*100)}%"></div>
                <div class="small mt-1 ${scoreClass(city.avg_weather_score)}">
                    Śr. score: ${city.avg_weather_score}
                </div>
            </div>
        </div>
    `).join("");
    document.getElementById("ranking").innerHTML = html;
}

async function loadEvents() {
    const cityId = document.getElementById("citySelect").value;
    const category = document.getElementById("categorySelect").value;
    const goodOnly = document.getElementById("goodWeatherOnly").checked;

    let url = `${API}/api/events?`;
    if (cityId) url += `city_id=${cityId}&`;
    if (category) url += `category=${encodeURIComponent(category)}&`;

    const res = await fetch(url);
    const data = await res.json();

    let events = data.events;
    if (goodOnly) events = events.filter(e => e.weather_score >= 75);

    clearMarkers();
    events.forEach(addMarker);

    const html = events.length === 0
        ? `<div class="col-12 text-center text-muted py-5">Brak wydarzeń</div>`
        : events.map(e => `
        <div class="col-md-4 mb-3">
            <div class="card p-3 h-100">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <span class="weather-icon">${weatherIcon(e.weather_main)}</span>
                    <span class="score-badge ${scoreClass(e.weather_score)}">${e.weather_score}/100</span>
                </div>
                <h6 class="fw-bold mb-1">${e.name}</h6>
                ${e.is_recurring ? `<span class="recurring-badge mb-1">🔁 Cykliczne</span>` : ""}
                <div class="small text-muted mb-1">📅 ${e.local_date} ${e.local_time ? "o " + e.local_time.slice(0,5) : ""}</div>
                <div class="small text-muted mb-1">📍 ${e.venue_name || "Brak danych"}</div>
                <div class="small text-muted mb-2">🎭 ${e.category}</div>
                <div class="small mb-2">
                    ${weatherIcon(e.weather_main)} ${e.weather_main} · 🌡️ ${e.temp}°C · 💨 ${e.wind_speed} m/s · 💧 ${e.humidity}%
                </div>
                ${e.url ? `<a href="${e.url}" target="_blank" class="btn btn-sm btn-outline-light mt-auto">Kup bilet →</a>` : ""}
            </div>
        </div>
    `).join("");

    document.getElementById("events").innerHTML = html;
}

document.getElementById("citySelect").addEventListener("change", loadEvents);
document.getElementById("categorySelect").addEventListener("change", loadEvents);
document.getElementById("goodWeatherOnly").addEventListener("change", loadEvents);

loadCities();
loadRanking();
loadEvents();
