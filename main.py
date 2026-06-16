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

#API:
from api.weather import get_weather
from api.news import get_news

# Boot up message
history = ConversationHistory(FAIRY_SYSTEM_PROMPT)
speak("Greetings, Master Proxy! Fairy online. Awaiting your request.")


#Intent (Use Case) handling

def handle_intent(intent: str, fairy_request: str) -> str | None:
    if intent == "weather":
        result = get_weather()
        speak(result)
        speak("If you'd like, master, I can open up AccuWeather to provide you with this encastire week's forecast for Cebu City")
        confirmation = listen_for_request()
        if confirmation and any(word in confirmation.lower() for word in ["yes", "sure", "go ahead", "open", "yeah", "please"]):
            import webbrowser
            webbrowser.open("https://www.accuweather.com/en/ph/cebu-city/264885/weather-forecast/264885")
            speak("Displaying week-long forecast for Cebu City. Please standby...")
        else:
            speak("Well, alright then. What else can I do for you, Master?")
        return ""   # Return empty string so main.py skips the LLM but doesn't crash
 
    if intent == "news":
        result = get_news()
        if not result:
            return "Master, I can't seem to retrieve any headlines."
        speak(result)
        speak("Want me to open a news page for the full story? I can pull up SunStar Cebu or Cebu Daily News.")
        confirmation = listen_for_request()
        if confirmation:
            import webbrowser
            text = confirmation.lower()
            if "sunstar" in text or "sun star" in text:
                webbrowser.open("https://www.sunstar.com.ph/cebu")
                speak("Opening SunStar Cebu for you, Master")
            elif "cdn" in text or "daily news" in text or "inquirer" in text:
                webbrowser.open("https://cebudailynews.inquirer.net/")
                speak("Opening Cebu Daily News for you, Master")
            elif any(word in text for word in ["yes", "sure", "go ahead", "yeah", "open"]):
                webbrowser.open("https://www.sunstar.com.ph/cebu")  # Default to SunStar
                speak("Opening SunStar Cebu for you, Master")
            else:
                speak("Well, alright then. What else can I do for you, Master?")
        return ""   # Same as above — skip LLM
 
    if intent == "reset":
        history.reset()
        return "Memory cleared, Master. Starting fresh."
 
    # All other intents (chat, zzz, system, etc.) → fall through to LLM
    return None

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
    print(f"[Intent]: {intent}") #Print out the user's intent

    if intent == "exit":
        speak("Systems shutting down. Bye for now, Master.")
        break

    #Intent-handling block
    direct_response = handle_intent(intent, fairy_request)
    if direct_response is not None #Intent was handled without an LLM. Catches both real responses and empty strings
        if direct_response:
            speak(direct_response)
        history.add_user(fairy_request) #Log the user's last message         # Only speak if there's actually something to say
        history.add_assistant(direct_response) #Direct response

    else:
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
                followup_intent = classify_intent(followup) #classify the intent of the follow up (if there is any)
                followup_direct = handle_intent(followup_intent, followup) #Handle the intent of the followup directly
        
                if followup_direct:
                    speak(followup_direct)
                    history.add_user(followup)
                    history.add_assistant(followup_direct)
                else:
                    history.add_user(followup)
                    followup_response = chat(history.get())
                    if followup_response and followup_response.strip():
                        history.add_assistant(followup_response)
                        speak(followup_response)
        # After the banter window, loop back to standby normally