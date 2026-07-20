import sys, os, re, random
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import GROQ_MODEL, FAIRY_GROQ_API_KEY
from groq import Groq
from entertainment.gaming.steam_client import get_owned_games, launch_game

groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

AFFIRM_WORDS  = ["yes", "yeah", "yep", "sure", "please", "go ahead", "okay", "ok", "boot it up"]
DECLINE_WORDS = ["no", "nah", "nope", "don't", "do not", "negative", "maybe later"]

def handle_gaming(voice_query: str, speak, get_user_input) -> str:
    try:
        games = get_owned_games()
    except Exception as e:
        print(f"[Gaming Error - Steam API]: {e}")
        return "I couldn't reach your Steam library just now, Master. Might be worth checking the API key."

    if not games:
        return "Your Steam library's looking empty from here, Master — check your profile's privacy settings if that's a surprise."

    pick, reason = _choose_recommendation(games)
    speak(_dynamic_line("recommend", name=pick["name"], reason=reason))

    speak(f"Would you like to play {pick['name']}, Master?")
    confirmation = get_user_input()

    if not confirmation or not confirmation.strip():
        return "No worries, Master — just say the word whenever you're ready."

    text = confirmation.lower()
    if _matches(text, AFFIRM_WORDS):
        try:
            launch_game(pick["appid"])
        except Exception as e:
            print(f"[Gaming Error - Launch]: {e}")
            return "I went to launch it, Master, but Steam didn't cooperate — might need a manual boot."
        return _dynamic_line("launch", name=pick["name"])

    if _matches(text, DECLINE_WORDS):
        return _dynamic_line("decline", name=pick["name"])

    return "Not quite sure what you meant there, Master — we can try again whenever."

#===== Helper Functions =====#

def _matches(text: str, phrases: list) -> bool:
    return any(re.search(r'\b' + re.escape(p) + r'\b', text) for p in phrases)

def _choose_recommendation(games: list):
    recent_candidates  = [g for g in games if g.get("playtime_2weeks", 0) > 0]
    backlog_candidates = [g for g in games if g.get("playtime_forever", 0) < 60]

    mode = random.choice(["recent", "backlog"])

    if mode == "recent" and recent_candidates:
        recent_sorted = sorted(recent_candidates, key=lambda g: g["playtime_2weeks"], reverse=True)
        top_pool = recent_sorted[:min(3, len(recent_sorted))]  # top 3 most-recently-played, not just #1
        return random.choice(top_pool), "recent"
    if backlog_candidates:
        return random.choice(backlog_candidates), "backlog"
    return random.choice(games), "random"  # Fallback if neither bucket had candidates

def _dynamic_line(action: str, name: str, reason: str = None) -> str:
    context_map = {
        "recommend_recent":  f"Fairy is recommending '{name}' because Master's been actively playing it lately.",
        "recommend_backlog": f"Fairy is recommending '{name}' because Master owns it but has barely touched it — nudging Master to finally give it a shot.",
        "recommend_random":  f"Fairy is recommending '{name}' from Master's library, just because.",
        "launch":  f"Fairy just launched '{name}' for Master via Steam.",
        "decline": f"Master declined to play '{name}' — Fairy is playfully accepting the rain check.",
    }
    key = f"recommend_{reason}" if action == "recommend" else action
    prompt = f"""You are Fairy, a voice assistant AI inspired by Zenless Zone Zero, addressing the user as Master or Master Proxy.
{context_map[key]}
Write ONE short, witty, spoken line (max 25 words) in Fairy's playful-but-efficient persona. No markdown, no quotation marks, just the line itself."""
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=70,
            temperature=0.9,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Gaming - Groq Error]: {e}")
        fallback = {
            "recommend_recent":  f"You've been on a roll with {name} lately, Master — want to keep going?",
            "recommend_backlog": f"You own {name} and barely touched it, Master. Maybe today's the day?",
            "recommend_random":  f"How about {name}, Master?",
            "launch":  f"Launching {name} now, Master.",
            "decline": f"Fair enough, Master — {name} will be there when you're ready.",
        }
        return fallback[key]
