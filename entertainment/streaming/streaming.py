import sys, os, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import GROQ_MODEL, FAIRY_GROQ_API_KEY, STREAMING_OTHER_SITE_URL
from groq import Groq
from entertainment.streaming.netflix_client import open_netflix_app
from entertainment.streaming.secure_session import open_protonvpn_app, open_browser_to
from brain.fairy_persona import NETFLIX_WATCHLIST

groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

NETFLIX_TRIGGERS    = ["netflix"]
OTHER_SITE_TRIGGERS = ["that site", "the other site", "other one", "that one", "the site"]

def handle_streaming(voice_query: str, speak, get_user_input) -> str:
    speak("Okay, Master. Would you like to go for Netflix, or would you like to go for... 'that site'?")
    choice = get_user_input()

    if not choice or not choice.strip():
        return "I didn't catch a choice there, Master. We can pick this up again whenever."

    text = choice.lower()

    if _matches(text, NETFLIX_TRIGGERS):
        return _handle_netflix(speak, get_user_input)

    if _matches(text, OTHER_SITE_TRIGGERS):
        return _handle_other_site()

    return "I wasn't sure which one you meant there, Master — Netflix, or 'that site'? Try again whenever you like."

#===== Helper Functions =====#

def _matches(text: str, phrases: list) -> bool:
    return any(re.search(r'\b' + re.escape(p) + r'\b', text) for p in phrases)


def _handle_netflix(speak, get_user_input) -> str:
    speak("What are you in the mood for tonight, Master?")
    mood = get_user_input()

    if not mood or not mood.strip():
        return "No worries, Master — just say the word whenever you know what you're after."

    try:
        open_netflix_app()
    except Exception as e:
        print(f"[Streaming - Netflix Launch Error]: {e}")
        return "I couldn't get Netflix open just now, Master. Might need a manual check."

    return _recommend_from_watchlist(mood)

def _recommend_from_watchlist(mood: str) -> str:
    prompt = f"""You are Fairy, a voice assistant AI inspired by Zenless Zone Zero, addressing the user as Master or Master Proxy.
Master just said they're in the mood for: "{mood}".
Here is Master's personal Netflix watchlist, grouped by genre:
{NETFLIX_WATCHLIST}
Pick 1-2 titles from this list that best fit the mood — use judgment on tone even if the
mood doesn't literally name a genre above. Write ONE short, playful, spoken line (max 25
words) announcing that Netflix is open and naming your pick(s) by title. No markdown, no
quotation marks, just the line itself. If nothing fits well, pick the closest genre anyway."""
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=70,
            temperature=0.8,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Streaming - Groq Error]: {e}")
        return "Netflix is open, Master — pick something good tonight."

def _handle_other_site() -> str:
    vpn_opened = True
    try:
        open_protonvpn_app()
    except Exception as e:
        print(f"[Streaming - VPN Launch Error]: {e}")
        vpn_opened = False
        return "I couldn't open ProtonVPN for you, Master. Looks like you'll have to proceed with caution here"

    try:
        open_browser_to(STREAMING_OTHER_SITE_URL)
    except Exception as e:
        print(f"[Streaming - Browser Error]: {e}")
        return "The VPN's up, Master, but I couldn't get the browser open. Might need a manual check."

    return _dynamic_line("other_site")

def _dynamic_line(branch: str, mood=None, titles=None) -> str:
    context_map = {
        "pause":  "Fairy just paused Master's music.",
        "netflix": f"Fairy just opened Netflix for Master after finding a few picks matching the mood '{mood}': {', '.join(titles)}.",
        "other_site_manual": "Fairy just opened ProtonVPN for Master to connect manually, and opened Firefox to their stand-in streaming site, ready and waiting.",
        "other_site_manual_novpn": "Fairy couldn't open ProtonVPN automatically, but still opened Firefox to Master's stand-in streaming site — Master should connect the VPN themselves first.",
    }
    prompt = f"""You are Fairy, a voice assistant AI inspired by Zenless Zone Zero, addressing the user as Master or Master Proxy.
{context_map[branch]}
Write ONE short, playful, spoken line (max 25 words) announcing this. No markdown, no quotation marks, just the line itself."""
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=70,
            temperature=0.9,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Streaming - Groq Error]: {e}")
        fallback = {
            "netflix": f"Found a few things matching '{mood}', Master — first up: {titles[0]}.",
            "other_site_manual": "VPN's up for you to connect, Master, and the browser's ready when you are.",
            "other_site_manual_novpn": "Couldn't find ProtonVPN, Master — but Firefox is open. Connect the VPN yourself first.",
        }
        return fallback[branch]