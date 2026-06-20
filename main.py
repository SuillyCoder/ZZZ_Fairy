#This is where the main program will be run; 
# where all the use cases will be implemented and called
#This will gradually be expanded as more use cases will be implemented

#Ollama Imports
from brain.ollama_client import chat
from brain.conversation import ConversationHistory
from brain.fairy_persona import FAIRY_SYSTEM_PROMPT
from brain.intent import classify_intent
from brain.session_state import SessionState
from brain.responses import get_greet_ack, get_wake_ack, get_empty_ack, get_confirmation_ack, get_shutdown_ack, get_decline_ack

# ============= USE CASE IMPORT CALLS ============ #

#Voice:
from voice.listener import listen_for_wakeword, listen_for_request
from voice.speaker import speak

#API:
from api.weather import get_weather
from api.news import get_news

#Gmail
from automation.email_handler import get_unread_emails, mark_all_fetched_as_read
from automation.finance import handle_finance

# Boot up message
history = ConversationHistory(FAIRY_SYSTEM_PROMPT)
session_state = SessionState()

speak(get_greet_ack())
confirm_triggers = ["yes", "sure", "go ahead", "open", "yeah", "please", "yes please", "please do"]

# TEMP — INPUT MODE TOGGLE (remove before MVP finalization)
speak("Please confirm if you would like to communicate via terminal or voice input")
print("\n=== FAIRY INPUT MODE ===")
print("1. Voice input")
print("2. Terminal input")
mode_choice = input("Select mode [1/2]: ").strip()

USE_TEXT_INPUT = (mode_choice == "2")
print(f"[Mode selected]: {'TEXT' if USE_TEXT_INPUT else 'VOICE'}\n")

#Function for handling the administered user input
def get_user_input(is_wakeword_check=False):
    if not USE_TEXT_INPUT:
        return listen_for_wakeword() if is_wakeword_check else listen_for_request()
        # Text mode: no wake word needed, no mic — just type directly
    if is_wakeword_check:
        text = input("[Type your request, or 'wake' to simulate wake word]: ").strip()
        return text  # Treated as if it were the "inline command" remainder
    else:
        return input("[You]: ").strip()
    

#Intent (Use Case) handling
def handle_intent(intent: str, fairy_request: str) -> str | None:
    if intent == "weather":
        result = get_weather()
        speak(result)
        speak("If you'd like, master, I can open up Ack-you-Weather to provide you with this entire week's forecast for Cebu City")
        confirmation = get_user_input()
        if confirmation and any(word in confirmation.lower() for word in confirm_triggers):
            import webbrowser
            speak(get_confirmation_ack())
            webbrowser.open("https://www.accuweather.com/en/ph/cebu-city/264885/weather-forecast/264885")
            speak("Displaying week-long forecast for Cebu City. Please standby...")
        else:
            speak("Well, alright then. What else can I do for you, Master?")
        session_state.update(intent="weather", topic="Cebu City weather", expects_followup=False)
        return ""   # Return empty string so main.py skips the LLM but doesn't crash
 
    if intent == "news":
        result = get_news()
        if not result:
            return "Master, I can't seem to retrieve any headlines."
        speak(result)
        speak("Want me to open a news page for the full story? I can pull up SunStar Cebu or Cebu Daily News.")
        confirmation = get_user_input()
        if confirmation:
            import webbrowser
            text = confirmation.lower()
            if "sunstar" in text or "sun star" in text:
                speak(get_confirmation_ack())
                webbrowser.open("https://www.sunstar.com.ph/cebu")
                speak("Opening SunStar Cebu for you, Master")
            elif "cdn" in text or "daily news" in text or "inquirer" in text:
                speak(get_confirmation_ack())
                webbrowser.open("https://cebudailynews.inquirer.net/")
                speak("Opening Cebu Daily News for you, Master")
            elif any(word in text for word in ["yes", "sure", "go ahead", "yeah", "open"]):
                speak(get_confirmation_ack())
                webbrowser.open("https://www.sunstar.com.ph/cebu")  # Default to SunStar
                speak("Opening SunStar Cebu for you, Master")
            else:
                speak("Well, alright then. What else can I do for you, Master?")
        return ""   # Same as above — skip LLM
 
    if intent == "email":
        result = get_unread_emails()
        speak(result)
 
        # Only offer to mark as read if there were actually unread emails
        if "no unread" not in result.lower() and "problem" not in result.lower() and "couldn't" not in result.lower():
            speak("Should I mark those as read, Master?")
            confirmation = get_user_input()
            if confirmation and any(word in confirmation.lower() for word in confirm_triggers):
                speak(get_confirmation_ack())
                mark_result = mark_all_fetched_as_read()
                speak(mark_result)
            else:
                speak("Alright. Leaving them as unread then.")
        return ""   # Skip LLM
    
    if intent == "finance":
        result = handle_finance(fairy_request)
        speak(result)
        return ""
    
    if intent == "reset":
        history.reset()
        session_state.reset()
        return "Memory cleared, Master. Starting fresh."
 
    # All other intents (chat, zzz, system, etc.) → fall through to LLM
    return None

# Main loop
while True:
    inline_command = get_user_input(is_wakeword_check=True)  # Standby until wake word is detected
    if inline_command and len(inline_command) > 3:
        # Command was already in the wake word sentence — use it directly
        fairy_request = inline_command
        print(f"[Inline command detected]: {fairy_request}")
    else:
        speak(get_wake_ack()) # Nothing after the wake word — listen for a separate request
        fairy_request = get_user_input()

    if not fairy_request:
        continue #Carry on if nothing was heard

    intent = classify_intent(fairy_request, session_state) #Tries to extract the intent based on STT input
    print(f"[Intent]: {intent}") #Print out the user's intent

    if intent == "exit":
        speak(get_shutdown_ack())
        break
    if intent == "decline":
        speak(get_decline_ack())
        history.add_user(fairy_request)
        history.add_assistant("Acknowledged.")
        continue

    #Intent-handling block
    direct_response = handle_intent(intent, fairy_request)
    if direct_response is not None: #Intent was handled without an LLM. Catches both real responses and empty strings
        if direct_response:
            speak(direct_response)
        history.add_user(fairy_request) #Log the user's last message         # Only speak if there's actually something to say
        history.add_assistant(direct_response) #Direct response

    else:
        history.add_user(fairy_request) #Log the user's last message
        response = chat(history.get()) #Formulate a response based on chat history

        # Guard against empty LLM responses
        if not response or not response.strip():
            speak(get_empty_ack())
            continue

        history.add_assistant(response) #Add the newly made response to the history
        speak(response) #Voice out the response

        #Banter window (for additional follow up) -> will edit more during Phase 4
        followup  = get_user_input()

        if followup and len(followup) > 3 and classify_intent(followup) != "exit":
                followup_intent = classify_intent(followup, session_state) #classify the intent of the follow up (if there is any)
                followup_direct = handle_intent(followup_intent, followup) #Handle the intent of the followup directly
        
                if followup_direct is not None:
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