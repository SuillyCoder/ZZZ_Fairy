import requests, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OWM_API_KEY

#OpenWeatherMap config settings

OWM_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
CITY = "Cebu City"
COUNTRY_CODE = "PH"
UNITS = "metric"

def get_weather() -> str:
    try: 
        params = {
            "q": f"{CITY},{COUNTRY_CODE}",  # City + country narrows search accuracy
            "appid": OWM_API_KEY,
            "units": UNITS,
        }
        response  = requests.get(OWM_BASE_URL, params=params, timeout=5) #Perform GET request
        response.raise_for_status() #Throws exception if HTTP is 4XX or 5XX
        data = response.json() #OWM returns JSON as parsed data

        # ── Extract the key fields ──
        temp        = round(data["main"]["temp"])
        feels_like  = round(data["main"]["feels_like"])
        humidity    = data["main"]["humidity"]
        description = data["weather"][0]["description"]   # e.g. "light rain"
        wind_speed  = round(data["wind"]["speed"] * 3.6)  # Convert m/s → km/h
        city_name   = data["name"]                        # OWM's confirmed city name
 
        # ── Format a short, spoken-friendly response ──
        spoken = (
            f"Current weather in {city_name}: {description}. "
            f"Temperature is {temp} degrees Celsius, feels like {feels_like}. "
            f"Humidity at {humidity} percent, wind at {wind_speed} kilometers per hour."
        )

        print(f"[Weather]: {spoken}")
        return spoken

    #EXCEPTION CASES:
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
