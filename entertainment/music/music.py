import sys, os, re, random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_MODEL, FAIRY_GROQ_API_KEY
from groq import Groq
import spotipy
from entertainment.music.spotify_client import (
    get_active_device_id, find_artist_uri, get_top_track_uris,
    play_context, play_tracks, pause_playback, resume_playback, skip_track, set_shuffle
)

groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

PAUSE_TRIGGERS  = ["pause", "stop the music", "stop playing", "stop the song"]
RESUME_TRIGGERS = ["resume", "unpause", "continue playing", "keep playing"]
SKIP_TRIGGERS   = ["skip", "next song", "next track", "change the song"]
DJ_TRIGGERS     = ["dj", "surprise me", "shuffle", "play something", "play music",
                    "play some music", "play me some music", "play a song", "random"]

def handle_music(voice_query: str) -> str:
    text = voice_query.lower()

    try:
        device_id = get_active_device_id()
    except Exception as e:
        print(f"[Music Error - Auth/Devices]: {e}")
        return "I couldn't reach Spotify, Master. The credentials or token might need a look."

    if device_id is None:
        return "I don't see Spotify open anywhere, Master. Open it on your phone or desktop, then ask again."

    try:
        if _matches(text, PAUSE_TRIGGERS):
            pause_playback(device_id)
            return _dynamic_line("pause")

        if _matches(text, RESUME_TRIGGERS):
            resume_playback(device_id)
            return _dynamic_line("resume")

        if _matches(text, SKIP_TRIGGERS):
            skip_track(device_id)
            return _dynamic_line("skip")

        if _matches(text, DJ_TRIGGERS):
            return _play_dj_mode(device_id)

        artist_name = _extract_artist(text)
        if artist_name:
            uri, resolved_name = find_artist_uri(artist_name)
            if uri:
                play_context(uri, device_id)
                return _dynamic_line("artist", name=resolved_name)
            return f"I couldn't find an artist called {artist_name}, Master."

        # Nothing specific parsed out — fall back to DJ mode rather than a dead end
        return _play_dj_mode(device_id)

    except spotipy.exceptions.SpotifyException as e:
        print(f"[Music - Spotify API Error]: {e}")
        return "Spotify didn't cooperate there, Master — might be worth checking your Premium status."
    except Exception as e:
        print(f"[Music Error]: {e}")
        return "Something went sideways trying to play that, Master."

# == Helper Functions == #

def _matches(text: str, phrases: list) -> bool: #Match comparator
    return any(re.search(r'\b' + re.escape(p) + r'\b', text) for p in phrases)

def _extract_artist(text: str): #Extracting artist details
        match = re.search(r"play (?:some (?:music by |songs by )?|me )?(.+)", text)
        if not match:
             return None
        candidate = re.sub(r"\b(music|songs|please|some|a song|a track)\b", "", match.group(1)).strip()
        return candidate or None

def _play_dj_mode(device_id: str) -> str:
    top_tracks = get_top_track_uris(limit = 20)
    if not top_tracks:
                return "I don't have enough listening history to spin something yet, Master."
    picks = random.sample(top_tracks, k=min(5, len(top_tracks)))
    
    try: #Disables shuffling (temporarily) in order to streamline song playlist
        set_shuffle(False, device_id)
    except Exception as e:
        print(f"[Music - Shuffle Toggle Error]: {e}")  # Non-critical — don't block playback over this
    
    play_tracks([p[0] for p in picks], device_id)
    _, track_name, artist_name = picks[0]
    return _dynamic_line("dj", track=track_name, artist=artist_name)

def _dynamic_line(action: str, name=None, track=None, artist=None) -> str:
    context_map = {
        "pause":  "Fairy just paused Master's music.",
        "resume": "Fairy just resumed Master's paused music.",
        "skip":   "Fairy just skipped to the next track for Master.",
        "artist": f"Fairy started playing music by '{name}' for Master, since Spotify doesn't expose its own 'DJ X' feature through the API.",
        "dj":     f"Fairy is standing in for Spotify's DJ X, since that feature isn't available via API. She just shuffled a set from Master's most-listened tracks, starting with '{track}' by {artist}.",
    }
    prompt = f"""You are Fairy, a voice assistant AI inspired by Zenless Zone Zero, addressing the user as Master or Master Proxy.
    {context_map[action]}
    Write ONE short, playful, spoken line (max 20 words) announcing this. No markdown, no quotation marks, just the line itself."""

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.9,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Music - Groq Error]: {e}")
        fallback = {
            "pause":  "Music paused, Master.",
            "resume": "Bringing the music back, Master.",
            "skip":   "Skipping ahead, Master.",
            "artist": f"Now playing {name}, Master.",
            "dj":     f"Spinning something for you, Master — starting with '{track}' by {artist}.",
        }
        return fallback[action]
