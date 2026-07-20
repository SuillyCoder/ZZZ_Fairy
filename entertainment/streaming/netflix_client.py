"""def search_netflix_catalog(moood_or_genre: str, limit: int=5) -> list:
    headers={ #Initialize the API key headers
        "X-RapidAPI-Key": NETFLIX_RAPIDAPI_KEY,
        "X-RapidAPI-Host": NETFLIX_RAPIDAPI_HOST,
    }
    params = {"query": moood_or_genre, "limit": limit} #Initialize two p[arameters: mood/genre and limit
    response = requests.get(
        f"https://{NETFLIX_RAPIDAPI_HOST}/search", #Instantiate the netflix client given the API keys
        headers=headers, params=params, timeout=10
    )
    response.raise_for_status() 
    data = response.json()

    #Display the corresponding data returned
    items = data.get("results") or data.get("data") or []
    titles = [item.get("title") for item in items[:limit] if item.get("title")]
    return titles """


import sys, os, subprocess, glob
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import NETFLIX_EXE_PATH

def find_netflix_exe():
    if NETFLIX_EXE_PATH and os.path.isfile(NETFLIX_EXE_PATH): #Check for the filepath for the Netflix shortcut
        return NETFLIX_EXE_PATH
    return None

def open_netflix_app(): 
    exe_path = find_netflix_exe #Extract the ProtonVPN file
    if not exe_path:
        raise RuntimeError("Couldn't locate ProtonVPN.exe — set PROTONVPN_EXE_PATH in your .env to the exact path.")
    os.startfile(exe_path) #Run a subprocess to open the shortcut path

