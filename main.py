#This is where the main program will be run; 
# where all the use cases will be implemented and called
#This will gradually be expanded as more use cases will be implemented

#Ollama Imports
from brain.ollama_client import chat
from brain.conversation import ConversationHistory
from brain.fairy_persona import FAIRY_SYSTEM_PROMPT
from brain.intent import classify_intent

# ============= USE CASE IMPORT CALLS ============ #

#Voice:
from voice.listener import listen_for_wakeword, listen_for_request
from voice.speaker import speak

# Boot up message
history = ConversationHistory(FAIRY_SYSTEM_PROMPT)
speak("Greetings, Master Proxy! Fairy online. Awaiting your request.")

# Main loop
while True:
    inline_command = listen_for_wakeword()  # Standby until wake word is detected
    if inline_command and len(inline_command) > 3:
        # Command was already in the wake word sentence — use it directly
        fairy_request = inline_command
        print(f"[Inline command detected]: {fairy_request}")
    else:
        speak("Yes, Master Proxy?") # Nothing after the wake word — listen for a separate request
        fairy_request = listen_for_request()

    if not fairy_request:
        continue #Carry on if nothing was heard

    intent = classify_intent(fairy_request) #Tries to extract the intent based on STT input

    if intent == "exit":
        speak("Systems shutting down. Bye for now, Master.")
        break

    history.add_user(fairy_request) #Log the user's last message
    response = chat(history.get()) #Formulate a response based on chat history

    # Guard against empty LLM responses
    if not response or not response.strip():
        speak("Sorry, I didn't get a response. Please try again.")
        continue

    history.add_assistant(response) #Add the newly made response to the history
    speak(response) #Voice out the response

    #Banter window (for additional follow up) -> will edit more during Phase 4
    followup  = listen_for_request()

    if followup and len(followup) > 3 and classify_intent(followup) != "exit":
        history.add_user(followup)
        followup_response = chat(history.get())

        if followup_response and followup_response.strip():
            history.add_assistant(followup_response)
            speak(followup_response)
    # After the banter window, loop back to standby normally