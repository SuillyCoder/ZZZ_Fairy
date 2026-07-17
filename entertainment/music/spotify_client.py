#Necessary imports
import sys, os, spotipy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, SPOTIFY_TOKEN_PATH

#Different capabilities of Spotify Client
SPOTIFY_SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "user-top-read",
    "user-library-read",
])

_sp_client = None

#Acquire the actual spotify client
def get_spotify_client() -> spotipy.Spotify:
    global _sp_client
    if _sp_client is not None:
        return _sp_client #Return the client if it exists
    
    #Acquire it if it doesn't exists beforehand (via authentication)
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_path=SPOTIFY_TOKEN_PATH,
        open_browser=True,
    )

    _sp_client = spotipy.Spotify(auth_manager=auth_manager)
    return _sp_client

def get_active_device_id(): #Returns an active device ID, or the first available one, or None if Spotify isn't open anywhere.
    sp = get_spotify_client() #Acquire the spotify client
    devices = sp.devices().get("devices", []) #Get the list of available devices
    if not devices:
        return None
    for d in devices:
        if d.get("is_active"): #Acquire the id of the device if it's active
            return d["id"]
    return devices[0]["id"] # None marked active — fall back to first available

def find_artist_uri(artist_name: str): #Helper function in order to find certain artists
    sp = get_spotify_client() #Acquire the client
    results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1) #Return just ONE
    items = results.get("artists", {}.get("items", [])) #Get all the corresponding item results
    if not items: 
        return None, None
    return items[0]["uri"], items[0]["name"] #Acquire all the items under a specific artist

def get_top_track_uris(limit=20):
    sp = get_spotify_client()
    results = sp.current_user_top_tracks(limit=limit, time_range="medium_term")
    return [(t["uri"], t["name"], t["artists"][0]["name"]) for t in results.get("items", [])]

#Different actions:

def play_context(context_uri: str, device_id: str): #Play playlist
    get_spotify_client().start_playback(device_id=device_id, context_uri=context_uri)

def play_tracks(uris: list, device_id: str): #Play tracks
    get_spotify_client().start_playback(device_id=device_id, uris=uris)

def pause_playback(device_id: str): #Pause the current track
    get_spotify_client().pause_playback(device_id=device_id)

def resume_playback(device_id: str): #Resume the track
    get_spotify_client().start_playback(device_id=device_id)

def skip_track(device_id: str): #Skip the current track
    get_spotify_client().next_track(device_id=device_id)

def set_shuffle(state: bool, device_id: str):
    get_spotify_client().shuffle(state, device_id=device_id)




