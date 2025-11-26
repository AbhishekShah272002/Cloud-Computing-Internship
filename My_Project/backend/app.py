# app.py
import os, requests
from flask import Flask, request, jsonify
from datetime import datetime
try:
    from google.cloud import firestore
    HAS_FIRESTORE = True
except Exception:
    HAS_FIRESTORE = False

app = Flask(__name__)
OWM_KEY = os.environ.get("OPENWEATHER_API_KEY")
if not OWM_KEY:
    raise RuntimeError("Set OPENWEATHER_API_KEY environment variable before running")

USE_FIRESTORE = os.environ.get("USE_FIRESTORE","false").lower() == "true"
db = None
if USE_FIRESTORE and HAS_FIRESTORE:
    db = firestore.Client()

def fetch_openweather(city):
    cur_url = "https://api.openweathermap.org/data/2.5/weather"
    fcast_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": OWM_KEY, "units": "metric"}
    cur = requests.get(cur_url, params=params, timeout=10); cur.raise_for_status()
    fcast = requests.get(fcast_url, params=params, timeout=10); fcast.raise_for_status()
    return cur.json(), fcast.json()

def process_weather(cur, fcast):
    current = {
        "city": cur.get("name"),
        "country": cur.get("sys", {}).get("country"),
        "temp_c": cur.get("main", {}).get("temp"),
        "humidity": cur.get("main", {}).get("humidity"),
        "wind_m_s": cur.get("wind", {}).get("speed"),
        "desc": cur.get("weather",[{}])[0].get("description"),
        "timestamp": cur.get("dt")
    }
    # collect up to 5 distinct date forecast points
    forecast_points = []
    seen = set()
    for item in fcast.get("list", []):
        date = item.get("dt_txt","").split(" ")[0]
        if date in seen: 
            continue
        forecast_points.append({
            "dt_txt": item.get("dt_txt"),
            "temp_c": item.get("main", {}).get("temp"),
            "humidity": item.get("main", {}).get("humidity"),
            "wind_m_s": item.get("wind", {}).get("speed"),
            "desc": item.get("weather",[{}])[0].get("description"),
        })
        seen.add(date)
        if len(forecast_points) >= 5:
            break
    return {"current": current, "forecast": forecast_points}

@app.route("/getWeather")
def get_weather():
    city = request.args.get("city")
    if not city:
        return jsonify({"error":"Missing city parameter. Use ?city=London"}), 400
    try:
        cur, fcast = fetch_openweather(city)
    except requests.HTTPError as e:
        return jsonify({"error":"OpenWeatherMap error","details":str(e)}), 502
    payload = process_weather(cur, fcast)
    payload["fetched_at"] = datetime.utcnow().isoformat() + "Z"
    if USE_FIRESTORE and db:
        doc_ref = db.collection("weather_history").document()
        doc_ref.set({"city":payload["current"].get("city"), "payload":payload})
    return jsonify(payload)

@app.route("/")
def root():
    return jsonify({"info":"Weather API: use /getWeather?city=<CityName>"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
