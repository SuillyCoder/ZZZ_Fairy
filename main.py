#This is where the main program will be run; 
# where all the use cases will be implemented and called
#This will gradually be expanded as more use cases will be implemented

# ============= USE CASE IMPORT CALLS ============ #

#Voice:
from voice.listener import listen_for_wakeword, listen_for_request
from voice.speaker import speak

# Boot up message
speak("Greetings, Master Proxy! Fairy online. Awaiting your request.")

# Main loop
while True:
    listen_for_wakeword()          # Standby until wake word is detected
    command = listen_for_request() # Capture the command
    speak(f"You said: {command}")  # Echo back for now — Ollama replaces this in Phase 3