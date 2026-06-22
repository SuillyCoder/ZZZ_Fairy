import re

# ── Intent keyword registry ──
# Each key is an intent name. Each value is a list of trigger phrases.
# The classifier scans the user's transcribed text for whole-word matches.
# "chat" has no keywords — it's the fallback when nothing else matches.

INTENT_KEYWORDS = {
    "exit":    ["quit", "exit", "shut down", "shutdown", "goodbye", "bye", "turn off", "turnoff", "power off", "poweroff", "go to sleep"],
    "weather": ["weather", "temperature", "rain", "forecast", "hot", "cold outside"],
    "news":    ["news", "headlines", "latest", "what happened", "latest news"],
    "email":   ["email", "emails", "mail", "inbox", "unread", "check my email", "any mail", "any emails", "do i have mail", "mark as read"],
    "finance": ["expense", "expenses", "spending", "spendings", "spent", "money", "budget", "finance", "financial", "tracker", "how much did i", "how much have i", "monthly", "category breakdown", "plot my", "chart my", "recommend", "trip spending", "japan trip", "summary report", "graph", "plot", "chart", "visualize", "visualise", "compare my", "comparison of my", "timeline", "superimposed", "breakdown"],
    "code":    ["review my code", "review the code", "review this file", "code review", "comment my code", "comment this file", "add comments", "auto comment", "commit message", "generate a commit", "git commit", "diagnose this error", "debug this", "fix this error", "refactor", "is this too long", "review the file at", "comment the file at"],
    "discord": ["discord", "server messages", "group chat", "group chats", "check discord", "discord messages", "any messages", "new messages", "check messages", "weirdos", "abode", "the abode", "weirdo's abode", "the weirdo's abode"],
    "reset":   ["forget everything", "clear history", "start over", "reset"],
    "zzz":     ["zenless", "zzz", "hoyoverse", "my account", "my characters", "showcase", "my agents", "my builds", "battery charge", "commission", "engagement", "weekly task", "banner", "next character", "upcoming character", "patch", "leaks", "leak", "rumor", "rumour", "announcement", "announcements"],
    "system":  ["battery", "cpu", "ram", "performance", "memory usage", "disk", "system status", "clear cache", "clear temp", "clear my cache", "free up space", "temp files", "task manager", "open task manager", "performance tab", "security check", "vulnerability", "security audit", "am i secure", "is my pc secure", "plot my performance", "plot performance", "graph my performance", "performance chart", "network usage", "chart my performance"],
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