"""Bounded background weather retrieval. No network calls on HID/render threads."""

from dataclasses import dataclass
import json
import locale
import math
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    country: str = ""
    timezone: str = ""
    source: str = "manual"


@dataclass(frozen=True)
class Weather:
    temperature: float  # Celsius internally
    condition: str
    wind: float  # km/h
    is_day: bool
    observed: float
    fetched: float


def local_country():
    value = locale.getlocale()[0] or ""
    code = value.rsplit("_", 1)[-1].upper()
    return code if len(code) == 2 and code.isalpha() else ""


def fetch_json(url):
    request = Request(url, headers={"User-Agent": "AgentStreamDeck weather", "Accept": "application/json"})
    with urlopen(request, timeout=5) as response:
        data = response.read(65537)
    if len(data) > 65536:
        raise ValueError("Weather response too large")
    return json.loads(data)


def number(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("Invalid weather value")
    return float(value)


def parse_location(data):
    if data.get("success") is not True:
        raise ValueError("Location unavailable")
    lat, lon = number(data.get("latitude"), -90, 90), number(data.get("longitude"), -180, 180)
    country = data.get("country_code", "")
    zone = data.get("timezone", {}).get("id", "")
    if not isinstance(country, str) or len(country) != 2:
        raise ValueError("Invalid location country")
    ZoneInfo(zone)
    return Location(lat, lon, country, zone, "ip")


def parse_weather(data, now):
    current = data["current"]
    temp = number(current.get("temperature_2m"), -100, 70)
    wind = number(current.get("wind_speed_10m"), 0, 500)
    code = number(current.get("weather_code"), 0, 99)
    valid_codes = {
        0,
        1,
        2,
        3,
        45,
        48,
        51,
        53,
        55,
        56,
        57,
        61,
        63,
        65,
        66,
        67,
        71,
        73,
        75,
        77,
        80,
        81,
        82,
        85,
        86,
        95,
        96,
        99,
    }
    if code not in valid_codes or type(current.get("is_day")) is not int or current["is_day"] not in (0, 1):
        raise ValueError("Unknown weather code/day flag")
    observed = number(current.get("time"), now - 86400, now + 900)
    condition = (
        "storm"
        if code >= 95
        else "snow"
        if code in (71, 73, 75, 77, 85, 86)
        else "rain"
        if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82)
        else "fog"
        if code in (45, 48)
        else "wind"
        if wind >= 35
        else "hot"
        if temp >= 32
        else "cloudy"
        if code in (2, 3)
        else "clear"
    )
    return Weather(temp, condition, wind, bool(current["is_day"]), observed, now)


class WeatherService:
    def __init__(self, options, fetch=fetch_json, clock=time.time):
        self.options, self.fetch, self.clock = options, fetch, clock
        self.location = None
        self.weather = None
        self.error = ""
        self.stop = threading.Event()
        self.thread = None
        self.located_at = 0.0
        self.lock = threading.Lock()
        if options["latitude"]:
            self.location = Location(
                float(options["latitude"]),
                float(options["longitude"]),
                "" if options["country"] == "auto" else options["country"],
                "" if options["timezone"] == "auto" else options["timezone"],
            )

    def refresh(self):
        o, now = self.options, self.clock()
        try:
            location = self.location
            if o["auto_location"] and not o["latitude"] and (location is None or now - self.located_at >= 86400):
                location = parse_location(self.fetch("https://ipwho.is/"))
                with self.lock:
                    self.location, self.located_at = location, now
            if not o["weather"] or o["weather_override"]:
                return
            if location is None:
                raise ValueError("Location needed")
            params = urlencode(
                dict(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    current="temperature_2m,weather_code,wind_speed_10m,is_day",
                    temperature_unit="celsius",
                    wind_speed_unit="kmh",
                    timeformat="unixtime",
                )
            )
            weather = parse_weather(self.fetch("https://api.open-meteo.com/v1/forecast?" + params), now)
            with self.lock:
                self.weather, self.error = weather, ""
        except Exception:
            # Provider errors must not leak IP/coordinates/URLs into logs or crash the broker.
            with self.lock:
                self.error = "Weather unavailable; check location or connection"

    def snapshot(self):
        with self.lock:
            weather, location, error = self.weather, self.location, self.error
        if weather and self.clock() - weather.observed > self.options["stale_seconds"]:
            weather = None
            error = "Weather expired"
        return location, weather, error

    def start(self):
        if self.thread is not None or not self.options["enabled"]:
            return
        if not self.options["auto_location"] and not (self.options["weather"] and self.location):
            return
        self.thread = threading.Thread(target=self._run, name="jelly-weather", daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop.is_set():
            self.refresh()
            self.stop.wait(self.options["poll_seconds"])

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=0.1)
