import re

#List of keywords based on use-cases
INTENT_KEYWORDS = {
    "exit":    ["quit", "exit", "shut down", "shutdown", "goodbye", "bye", "turn off", "turnoff", "power off", "poweroff", "go to sleep"],
    "weather": ["weather", "temperature", "rain", "forecast", "hot", "cold outside"],
    "news":    ["news", "headlines", "latest", "what happened"],
    "reset":   ["forget everything", "clear history", "start over", "reset"],
    "zzz":     ["zenless", "zzz", "hoyoverse", "my account", "my characters"],
    "system":  ["battery", "cpu", "ram", "performance", "memory usage", "disk"],
    "chat":    [],  # Default fallback — no keywords needed
}

def classify_intent(text: str) -> str:
    text_lower = text.lower() #Normalizes capitalization
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent == "chat": #If the user's intent is a chat
            continue #Skip the fallback
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower): #checks if an intent keyword is anywhere within the text.
                return intent
    return "chat"