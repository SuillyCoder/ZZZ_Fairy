import sys, os, requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import STEAM_API_KEY, STEAM_ID

def get_owned_games() -> list:
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": STEAM_ID,
        "format": "json",
        "include_appinfo": True,
        "include_played_free_games": True,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json().get("response", {}).get("games", [])

def launch_game(appid: int):
    os.startfile(f"steam://rungameid/{appid}")
