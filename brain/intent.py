import re

# ── Intent keyword registry ──
# Each key is an intent name. Each value is a list of trigger phrases.
# The classifier scans the user's transcribed text for whole-word matches.
# "chat" has no keywords — it's the fallback when nothing else matches.

INTENT_KEYWORDS = {
    "exit":    ["quit", "exit", "shut down", "shutdown", "goodbye", "bye", "turn off", "turnoff", "power off", "poweroff", "go to sleep"],
    "weather": ["weather", "temperature", "rain", "forecast", "hot", "cold outside"],
    "news":    ["news", "headlines", "latest", "what happened"],
    "email":   ["email", "emails", "mail", "inbox", "unread", "check my email", "any mail", "any emails", "do i have mail", "mark as read"],
    "finance": ["expense", "expenses", "spending", "spent", "money", "budget", "finance", "financial", "tracker", "how much did i", "monthly", "category breakdown", "plot my", "chart my", "recommend", "trip spending", "japan trip", "summary report"],
    "reset":   ["forget everything", "clear history", "start over", "reset"],
    "zzz":     ["zenless", "zzz", "hoyoverse", "my account", "my characters"],
    "system":  ["battery", "cpu", "ram", "performance", "memory usage", "disk"],
    "chat":    [],  # Default fallback — no keywords needed
}

def classify_intent(text: str, session_state=None) -> str:
    text_lower = text.lower()

    if session_state is not None: #If a session is happening
        resolved = session_state.resolve_followup(text) #Load in a session state yet to be resolved by Fairy
        if resolved is not None:
            return resolved

    for intent, keywords in INTENT_KEYWORDS.items():
        if intent == "chat":
            continue
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                return intent
    return "chat"