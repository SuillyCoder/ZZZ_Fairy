import os, sys, asyncio, json, time, threading, requests, genshin, ssl, aiohttp

#Import absolute filepath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ZZZ_UID, HOYOLAB_LTUID, HOYOLAB_LTOKEN, FAIRY_GROQ_API_KEY, GROQ_MODEL, BASE_DIR

from groq import Groq
groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

#Base Urls for Enka.net and Ennead 
ENKA_BASE_URL = "https://enka.network/api/zzz/uid"
ENNEAD_BASE_URL = "https://api.ennead.cc/mihoyo/zenless" 

#Fetching parameters
ZZZ_NEWS_LIMIT = 6
ENERGY_NUDGE_THRESHOLD = 0.9 

#Agent Name via json lookup table
ENKA_AVATARS_URL = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/zzz/avatars.json"
ENKA_LOCS_URL = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/zzz/locs.json"
AGENT_CACHE_PATH = os.path.join(BASE_DIR, "zenless", "_zzz_agent_cache.json")
os.makedirs(os.path.dirname(AGENT_CACHE_PATH), exist_ok=True)

AGENT_CACHE_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days — agent rosters change roughly per patch, not daily

last_showcase_fetch = 0.0
SHOWCASE_COOLDOWN_SECONDS = 65  # just over Enka's ~60s cache window


# ========== Authentication ============ #

def build_hoyolab_client() -> genshin.Client:
    client = genshin.Client(
        {"ltuid_v2": HOYOLAB_LTUID, "ltoken_v2": HOYOLAB_LTOKEN}, #Extract the cookie pointer for the user (me)
        game=genshin.types.Game.ZZZ, #Set the game to fetch data about to Zenless Zone Zero
        uid=int(ZZZ_UID) if ZZZ_UID else None, #Fetch the specific ZZZ UID
    )
    return client

def validate_hoyolab_cookies() -> bool: #Validate the passed cookies
    if not (HOYOLAB_LTUID and HOYOLAB_LTOKEN): #If the cookies do not match
        print("[ZZZ]: HoYoLAB cookies not configured — skipping validation.")
        return False
    try:
        client = build_hoyolab_client() #Construct the client\
        asyncio.run(client.get_zzz_notes())
        print("[ZZZ]: HoYoLAB session validated successfully.") #Successful ZZZ Client Creation
        return True
    #Exception throwing
    except genshin.errors.InvalidCookies:
        print("[ZZZ Warning]: HoYoLAB cookies are invalid or expired. Refresh ltuid_v2/ltoken_v2 in .env.")
        return False
    except Exception as e:
        print(f"[ZZZ Warning]: Could not validate HoYoLAB session at boot — {e}")
        return False
    
# Agent lookup via json lookup table
def fetch_zzz_agents() -> dict[str, str]: #Returns a dictionary (Char ID and Name) for the complete reference table
    avatars_resp = requests.get(ENKA_AVATARS_URL, timeout=10) #Fetch the avatars from EnkaNetwork
    avatars_resp.raise_for_status()
    avatars = avatars_resp.json()

    locs_resp = requests.get(ENKA_LOCS_URL, timeout=10) #Fetch the locations (idk what locations they mean, but okay...)
    locs_resp.raise_for_status()
    en_locs = locs_resp.json().get("en", {})
 
    lookup = {} #Lookup table 
    for agent_id, info in avatars.items():
        codename = info.get("Name", "") #Fetch their name
        display_name = en_locs.get(codename) #Get their actual display name
        if display_name:
            lookup[agent_id] = display_name
    return lookup

def get_zzz_agents() -> dict[str, str]: #Returns their actual display name using a 7-day local disk cache
    cached = None
    if os.path.exists(AGENT_CACHE_PATH):
        try:    
            with open(AGENT_CACHE_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
        except:
            cached = None
    cache_is_fresh = (
        cached is not None and (time.time() - cached.get("_fetched_at", 0)) < AGENT_CACHE_TTL_SECONDS
    )

    if cache_is_fresh: #Checks for the freshness of the cache
        return cached["lookup"]

    try:
        lookup = fetch_zzz_agents()
        with open(AGENT_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"_fetched_at": time.time(), "lookup": lookup}, f)
        return lookup
    except requests.exceptions.RequestException as e:
        print(f"[ZZZ Agent Lookup]: Refresh failed ({e}), using stale cache if available.")
        if cached is not None:
            return cached["lookup"]
        return {}
    
def get_character_showcase() -> str: #Acquire showcase of ZZZ Character Roster

    #Rate limiting to not retrieve requests too frequently
    global last_showcase_fetch #Global variable of last showcase
    now = time.time() #Get the current time
    if now - last_showcase_fetch < SHOWCASE_COOLDOWN_SECONDS: #If current fetched time is lesser than preset cooldown time
        remaining = int(SHOWCASE_COOLDOWN_SECONDS - (now - last_showcase_fetch)) #Calculate remaining time
        return f"I just checked your showcase, Master. Enka needs about {remaining} more seconds before I can refresh it." #Flag rate limiting prompt
    last_showcase_fetch = now #Set the time to last showcase to the current time

    if not ZZZ_UID: 
        return "I don't have your ZZZ UID configured, Master. Add ZZZ_UID to the .env file."
    try:
        resp = requests.get (f"{ENKA_BASE_URL}/{ZZZ_UID}/", timeout=10) #Acquire the ZZZ UID via fetching from Enka Network and your hard-coded UID Value
        if resp.status_code == 404: #Could not find it at all
            return "That UID doesn't seem to exist, Master. Double-check it."
        if resp.status_code == 429: #Too many requests
             return "Enka is rate-limiting us right now, Master. Try again in a bit."
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[ZZZ Enka Error]: {e}")
        return "I couldn't reach Enka Network just now, Master."
    
    player = data.get("PlayerInfo", {}) #Extract player information
    showcase = player.get("ShowcaseDetail", {}) #Extract that said player's character showcase
    agents = showcase.get("AvatarList", []) #Extract the characters within that showcase
    profile = player.get("SocialDetail", {}).get("ProfileDetail", {})
    nickname = profile.get("Nickname", "your account")
    level = profile.get("Level", "unknown")

    if not agents: #Checking if no agents are found within the display
        return (
            f"I reached {nickname}'s profile — Inter-Knot level {level} — "
            "but no agents are in the public showcase, Master."
        )
    count = len(agents)
    lookup = get_zzz_agents()

    sorted_agents = sorted(agents, key=lambda a: a.get("Level", 0), reverse=True)
    named = []
    for a in sorted_agents[:3]:
        agent_id = str(a.get("Id", ""))
        name = lookup.get(agent_id, f"agent {agent_id}")
        named.append(f"{name} at level {a.get('Level', '?')}")

    spoken = (  #Speak out the Enka.net extracted results
        f"{nickname} is Inter-Knot level {level}, with {count} agent"
        f"{'s' if count != 1 else ''} in the public showcase, Master. "
        f"Top agents: {', '.join(named)}."
    )
    return spoken
    
# ========== HOYOLAB HELPERS ============= #

#ZZZ Account Status
def get_account_status() -> str:
    if not (HOYOLAB_LTUID and HOYOLAB_LTOKEN): #Flag if the cookie pointers have been set up to open Hoyolab
        return "HoYoLAB isn't set up yet, Master. Add your ltuid_v2 and ltoken_v2 to the .env file."

    try: 
        client = build_hoyolab_client()
        notes = asyncio.run(client.get_zzz_notes())
    except genshin.errors.InvalidCookies:
        return "My HoYoLAB session has expired, Master. Please refresh the cookies in .env."
    except Exception as e:
        print(f"[ZZZ HoYoLAB Error]: {e}")
        return "I ran into a problem reaching HoYoLAB, Master."
    
    parts = []
    parts.append(f"Battery charge is at {notes.battery_charge.current} out of {notes.battery_charge.max}.") #Check for battery charge
    parts.append(f"Daily engagement is {notes.engagement.current} out of {notes.engagement.max}.") #Check for daily engagement

    if notes.weekly_task:
        parts.append(f"Weekly task progress is {notes.weekly_task.cur_point} out of {notes.weekly_task.max_point}.")
    return " ".join(parts) + " That's your status, Master."

#ZZZ Banner Status
def get_banner_status() -> str:
    try:
        resp = requests.get(f"{ENNEAD_BASE_URL}/calendar", params={"lang": "en-us"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[ZZZ Calendar Error]: {e}")
        return "I couldn't reach the banner schedule just now, Master."
    except Exception as e:
        print(f"[ZZZ Banner Unexpected Error]: {e}")
        return "Something went wrong checking the banners, Master."
 
    #Extract the current banners and list them out
    banners = data.get("banners", [])
    character_banners = [b for b in banners if b.get("banner_type") == "GACHA_TYPE_CHARACTER_UP"]

    if not character_banners:
        return "I don't see any active character banners right now, Master."

    spoken_parts = []
    for banner in character_banners[:2]:
        names = ", ".join(a.get("name", "") for a in banner.get("agents", []) if a.get("name"))
        end_time = banner.get("end_time", 0)
        days_left = max(int((end_time - time.time()) // 86400), 0)
        spoken_parts.append(
            f"{names or 'A banner'} has {days_left} day{'s' if days_left != 1 else ''} remaining"
        )
 
    return ". ".join(spoken_parts) + ", Master."

#ZZZ News and Updates
def get_latest_zenless_news() -> str:
    try: 
        resp = requests.get(f"{ENNEAD_BASE_URL}/news/notices", params={"lang": "en-us"}, timeout=10)
        resp.raise_for_status()
        notices = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[ZZZ News Error]: {e}")
        return "I couldn't reach the news feed just now, Master."
    except Exception as e:
        print(f"[ZZZ News Unexpected Error]: {e}")
        return "Something went wrong fetching ZZZ news, Master."
    
    if not notices: 
        return "Nothing new from official channels right now, Master."

    titles = [n.get("title", "") for n in notices[:ZZZ_NEWS_LIMIT] if n.get("title")]
    if not titles:
        return "Nothing new from the official channels right now" 
    bulleted = "\n".join(f"- {t}" for t in titles)
    try: 
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                "role": "system",
                "content": (
                    "You are summarizing recent official Zenless Zone Zero HoYoLAB "
                    "notice titles into a short, spoken-style summary for a voice assistant. "
                    "2-3 sentences max. Mention only what's actually in the titles — "
                    "don't invent details."
                ),
            }, {
                "role": "user",
                "content": bulleted,
            }],
            max_tokens=200,
        )
        summary = completion.choices[0].message.content.strip()
    except Exception as e: 
        print(f"[ZZZ Groq Error]: {e}")
        summary = f"Here's the latest: {titles[0]}"
 
    return f"{summary} Want me to open the full notice for you, Master?"

# ===== Proactive Monitor for ZZZ Flags ======#
energy_nudge_fired = False #Checks if the nudge for the energy cap has been fired
last_seen_banner_id = None #Checks the most recently seen banner

def check_zzz_nudges() -> str | None:
    global energy_nudge_fired, last_seen_banner_id

    #ENERGY NUDGE CHECKER
    if HOYOLAB_LTUID and HOYOLAB_LTOKEN:
        try:
            client = build_hoyolab_client()
            notes = asyncio.run(client.get_zzz_notes())
            if notes.battery_charge.max > 0:
                ratio = notes.battery_charge.current / notes.battery_charge.max
                if ratio >= ENERGY_NUDGE_THRESHOLD:
                    if not energy_nudge_fired:
                        energy_nudge_fired = True
                        return (f"Master, your battery charge is at {notes.battery_charge.current} out of "
                            f"{notes.battery_charge.max} — close to capping. You might want to spend it.")
                else:
                    energy_nudge_fired = False
        except Exception as e: 
            print(f"[ZZZ Monitor Error - energy check]: {e}")

    #BANNER NUDGE CHECKER
    try:
        resp = requests.get(f"{ENNEAD_BASE_URL}/calendar", params={"lang": "en-us"}, timeout=10) #Get banner information via the ennead mihoyo api
        resp.raise_for_status()
        banners = resp.json().get("banners", [])
        character_banners = [b for b in banners if b.get("banner_type") == "GACHA_TYPE_CHARACTER_UP"] #Returns all the current banners withint the parsed json

        if character_banners:
            current = character_banners[0]
            current_id = (
                tuple(a.get("name") for a in current.get("agents", [])), #Acquire the agents in that banner
                current.get("start_time"), #Acquire the run time and remaining time
            )

        if last_seen_banner_id is None:
                # First check this run — just record it, don't nudge yet
                last_seen_banner_id = current_id
        elif current_id != last_seen_banner_id:
                last_seen_banner_id = current_id
                names = ", ".join(a.get("name", "") for a in current.get("agents", []) if a.get("name"))
                return f"Master, a new banner just went live featuring {names or 'a new agent'}."

    except requests.exceptions.RequestException as e: 
        print(f"[ZZZ Monitor Error - banner check]: {e}")
    except Exception as e:
        print(f"[ZZZ Monitor Unexpected Error - banner check]: {e}")
    return None

# Monitor startup 
def start_zzz_monitor(speak_fn, poll_interval=3600): #Daemon polling for ZZZ info monitoring
    def loop():
        while True:
            nudge = check_zzz_nudges()
            if nudge:
                speak_fn(nudge)
            threading.Event().wait(poll_interval) #Allocate some time for the thread to wait via polling
    thread = threading.Thread(target=loop, daemon=True) #Run a daemon thread
    thread.start()
    return thread

# Entry poiont (sub-intent dispatch)
def handle_zzz(voice_query: str) -> str:
    text = voice_query.lower()

    if any(w in text for w in ["leak", "leaks", "news", "announcement", "announcements", "rumor", "rumour"]):
        return get_latest_zenless_news()
 
    if any(w in text for w in ["banner", "patch", "next character", "upcoming character"]):
        return get_banner_status()
 
    if any(w in text for w in ["showcase", "characters", "agents", "builds"]):
        return get_character_showcase()
 
    if any(w in text for w in ["battery", "commission", "engagement", "status", "weekly task", "my account"]):
        return get_account_status()
 
    # Default fallback — general status
    return get_account_status()