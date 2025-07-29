import json, os
from flask import Flask, render_template
from redis import Redis
import requests

app = Flask(__name__)
redis = Redis(host="redis", port=6379, decode_responses=True)

# --- API Open‑Meteo ----------------------------------------------------------
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
LAT       = os.getenv("LAT", "-22.2758")           # Nouméa
LON       = os.getenv("LON", "166.4579")
TIMEZONE  = os.getenv("TIMEZONE", "Pacific/Noumea")
CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))      # 10 min

@app.route("/")
def index():
    visits = redis.incr("hits")

    cached = redis.get("weather")
    if cached is None:
        params = {
            "latitude": LAT,
            "longitude": LON,
            "current": "temperature_2m",
            "timezone": TIMEZONE,
        }
        r = requests.get(WEATHER_URL, params=params, timeout=10)
        r.raise_for_status()
        redis.set("weather", json.dumps(r.json()), ex=CACHE_TTL)
        data = r.json()
    else:
        data = json.loads(cached)

    current = data["current"]
    return render_template(
        "index.html",
        visits=visits,
        temperature=current["temperature_2m"],
        weather_time=current["time"],
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
