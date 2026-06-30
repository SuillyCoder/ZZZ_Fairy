import requests, sys, os
from datetime import datetime
from groq import Groq

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OWM_API_KEY, GROQ_MODEL, FAIRY_GROQ_API_KEY

groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

#OpenWeatherMap config settings

OWM_CURRENT_URL  = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
CITY = "CEBU CITY"
COUNTRY_CODE = "PH"
UNITS = "metric"


def get_weather(voice_query: str = "") -> str:
    try:
        current_data  = _fetch_current()
        forecast_data = _fetch_forecast()
    #EXCEPTION CASES (unchanged strings — main.py's weather_failed check depends on these):
    except requests.exceptions.ConnectionError:
        return "I couldn't reach the weather service. Check your internet connection, Master."

    except requests.exceptions.Timeout:
        return "The weather request timed out. Try again in a moment."

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status == 401:
            return "My weather API key seems to be invalid. Update it in api/weather.py."
        elif status == 404:
            return "I couldn't find weather data for Cebu City. That's unusual."
        else:
            return f"Weather API returned an error. Status code {status}."

    except (KeyError, IndexError):
        return "I got a weather response but couldn't parse it properly. The API format may have changed."

    except Exception as e:
        print(f"[Weather Error]: {e}")
        return "Something went wrong while fetching the weather."

    # Build the deterministic fallback FIRST, from real data, before touching Groq.
    fallback_spoken = _build_fallback_response(current_data)

    try:
        spoken = _generate_dynamic_response(voice_query, current_data, forecast_data)
        print(f"[Weather]: {spoken}")
        return spoken
    except Exception as e:
        print(f"[Weather - Groq Error]: {e}")
        print(f"[Weather]: {fallback_spoken}")
        return fallback_spoken

#===== Helper Functions ====#

def _fetch_current() -> dict:
    """Raw current-conditions fetch — raises on failure, same as before."""
    params = {
        "q": f"{CITY},{COUNTRY_CODE}",
        "appid": OWM_API_KEY,
        "units": UNITS,
    }
    response = requests.get(OWM_CURRENT_URL, params=params, timeout=5)
    response.raise_for_status()
    return response.json()


def _fetch_forecast() -> dict:
    try:
        params = {
            "q": f"{CITY},{COUNTRY_CODE}",
            "appid": OWM_API_KEY,
            "units": UNITS,
        }
        response = requests.get(OWM_FORECAST_URL, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[Weather - Forecast Error]: {e}")
        return {}


def _build_fallback_response(data: dict) -> str:
    """The original, deterministic current-conditions template. Used if Groq fails."""
    temp        = round(data["main"]["temp"])
    feels_like  = round(data["main"]["feels_like"])
    humidity    = data["main"]["humidity"]
    description = data["weather"][0]["description"]
    wind_speed  = round(data["wind"]["speed"] * 3.6)
    city_name   = data["name"]

    return (
        f"Current weather in {city_name}: {description}. "
        f"Temperature is {temp} degrees Celsius, feels like {feels_like}. "
        f"Humidity at {humidity} percent, wind at {wind_speed} kilometers per hour."
    )


def _summarize_forecast_by_day(forecast_data: dict) -> str:
    if not forecast_data or "list" not in forecast_data:
        return "No forecast data available."

    days: dict[str, dict] = {}
    for entry in forecast_data["list"]:
        date_str = entry["dt_txt"].split(" ")[0]  # "YYYY-MM-DD"
        temp = entry["main"]["temp"]
        desc = entry["weather"][0]["description"]

        if date_str not in days:
            days[date_str] = {"temps": [], "descs": []}
        days[date_str]["temps"].append(temp)
        days[date_str]["descs"].append(desc)

    lines = []
    for date_str, vals in days.items():
        weekday = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
        low  = round(min(vals["temps"]))
        high = round(max(vals["temps"]))
        most_common_desc = max(set(vals["descs"]), key=vals["descs"].count)
        lines.append(f"{weekday} ({date_str}): {low}-{high}°C, {most_common_desc}")

    return "\n".join(lines)


def _generate_dynamic_response(voice_query: str, current_data: dict, forecast_data: dict) -> str:
    today_str = datetime.now().strftime("%A, %B %d, %Y")

    current_summary = (
        f"City: {current_data['name']}\n"
        f"Condition: {current_data['weather'][0]['description']}\n"
        f"Temperature: {round(current_data['main']['temp'])}°C "
        f"(feels like {round(current_data['main']['feels_like'])}°C)\n"
        f"Humidity: {current_data['main']['humidity']}%\n"
        f"Wind: {round(current_data['wind']['speed'] * 3.6)} km/h"
    )

    forecast_summary = _summarize_forecast_by_day(forecast_data)

    prompt = f"""You are Fairy, a voice assistant. Today is {today_str}. The user asked: "{voice_query}"

Here is the ONLY real weather data you are allowed to use. Do not invent, guess, or
add any number, condition, or day that is not explicitly listed below:

CURRENT CONDITIONS (Cebu City, right now):
{current_summary}

5-DAY FORECAST (daily low-high range and condition):
{forecast_summary}

Instructions:
- Figure out from the user's question whether they want TODAY's current conditions,
  a SPECIFIC day (e.g. "Wednesday", "tomorrow"), or the WEEK AHEAD overview.
- If they didn't specify a timeframe, or their question doesn't relate to weather, default to today's current conditions.
- If they ask about a day or range outside the 5-day forecast window provided, say
  you don't have data that far out yet — don't make anything up.
- Respond in ONE short, natural, spoken sentence or two. No markdown, no bullet points.
- Stay in character: efficient, a little playful, address the user as "Master" or
  similar, the way Fairy normally talks.
- Use ONLY the numbers and conditions given above. Never fabricate data."""

    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.4,
    )
    return completion.choices[0].message.content.strip()