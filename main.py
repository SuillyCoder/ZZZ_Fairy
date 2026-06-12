#This is where the main program will be run; 
# where all the use cases will be implemented and called
#This will gradually be expanded as more use cases will be implemented

# ============= USE CASE IMPORT CALLS ============ #

#Voice:
from voice.listener import listen_for_wakeword, listen_for_request
from voice.speaker import speak
import time

# Boot up message
speak("Greetings, Master Proxy! Fairy online. Awaiting your request.")

# Main loop
while True:
    listen_for_wakeword()          # Standby until wake word is detected
    speak("Yes, Master Proxy?")       # Audio cue — start speaking after this
    fairy_request = listen_for_request() # Capture the command
    if fairy_request:
        speak(f"You said: {fairy_request}")  # Echo back for now — Ollama replaces this in Phase 3