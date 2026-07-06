#This is where the main program will be run; 
# where all the use cases will be implemented and called
#This will gradually be expanded as more use cases will be implemented

#===== Ollama Imports ===== #
from brain.ollama_client import chat
from brain.conversation import ConversationHistory
from brain.fairy_persona import FAIRY_SYSTEM_PROMPT
from brain.intent import classify_intent
from brain.session_state import SessionState
from brain.responses import get_greet_ack, get_wake_ack, get_empty_ack, get_confirmation_ack, get_shutdown_ack, get_decline_ack
from datetime import datetime
from zoneinfo import ZoneInfo
PH_TIMEZONE = ZoneInfo("Asia/Manila")  # Philippine Time — same zone as Cebu City

# ============= USE CASE IMPORT CALLS ============ #

#==== Voice: ====#
from voice.listener import listen_for_wakeword, listen_for_request
from voice.speaker import speak

#==== API: ====#
from api.weather import get_weather
from api.news import get_news, search_news, extract_news_topic

#==== Automation: ====#
from automation.email_handler import get_unread_emails, mark_all_fetched_as_read
from automation.finance import handle_finance
from automation.discord_handler import get_recent_discord_messages
from automation.code_assistant import (review_code, generate_commented_version, apply_commented_version, discard_commented_version, generate_commit_message, confirm_commit, diagnose_error, suggest_refactor)

#==== Hardware and Device: ====#
from device.system_info import (get_system_performance, check_battery_threshold, start_battery_monitor, preview_cache_clear, clear_cache, open_task_manager_performance)
from device.performance_plot import plot_performance_metrics
from device.security_audit import run_security_audit

#==== Zenless Zone Zero: ======#
from zenless.zzz_tracker import handle_zzz, validate_hoyolab_cookies, start_zzz_monitor

# ======= Computer Vision ========= #
from computer_vision.sleep_alarm.SleeperAlarm import handle_sleep_alarm

# ==== Bridge Import ===== #
from gui.bridge import fairy_bridge

# Extraction handler
import re as _re_path_extract
import os, time

from birthday import happy_birthday

#MAIN EXECUTABLE CODE
def run():
    # Boot up message
    history = ConversationHistory(FAIRY_SYSTEM_PROMPT)
    session_state = SessionState()
    validate_hoyolab_cookies()  # Validate the hoyolab cookies in advance

    #Boot up asynchronous threads
    start_zzz_monitor(speak, poll_interval=3600)
    start_battery_monitor(speak, poll_interval=60)

    speak(get_greet_ack())

    #Checks if it's your birthday
    happy_birthday()

    affirm_triggers = ["yes", "sure", "go ahead", "open", "yeah", "please", "yes please", "please do"]
    decline_triggers = ["no", "nope", "no thanks", "no fairy", "don't", "dont", "do not", "no please", "no thank you"]

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
        
    def extract_path(text: str) -> str | None:
        # Quoted path takes priority if present
        quoted = _re_path_extract.search(r'["\']([^"\']+)["\']', text)
        if quoted:
            return quoted.group(1).strip()
    
        # Windows-style path: C:/... or C:\...
        win_path = _re_path_extract.search(r'[A-Za-z]:[\\/][^\s]+', text)
        if win_path:
            return win_path.group(0).strip().rstrip(".,?!")
    
        # Bare relative path with a slash or a file extension
        bare_path = _re_path_extract.search(r'\S+\.(py|js|ts|java|cpp|c|cs|go|rb|php|html|css)\b', text)
        if bare_path:
            return bare_path.group(0).strip().rstrip(".,?!")
    
        return None

    pending_comment_preview = {"filepath": None, "temp_path": None}
    pending_commit = {"repo_path": None, "message": None}
    
        

    #Intent (Use Case) handling
    def handle_intent(intent: str, fairy_request: str) -> str | None:
        if intent == "time":
            now_ph = datetime.now(PH_TIMEZONE)
            text = fairy_request.lower()
            wants_date = any(w in text for w in ["date", "day is it", "day today"])
            wants_time = "time" in text
            if wants_date and not wants_time:
                return now_ph.strftime("Today is %A, %B %d, %Y, Master.")
            # Default to time (also covers "what time is it" and ambiguous phrasing).
            # Built manually rather than via %-I/%#I, since those strftime flags
            # aren't portable to Windows (this project runs on Windows).
            hour_12 = now_ph.hour % 12 or 12
            return f"It's {hour_12}:{now_ph.minute:02d} {now_ph.strftime('%p')} Philippine Time, Master."

        if intent == "weather":
            result = get_weather(fairy_request)
            speak(result)

            # Known error strings returned by get_weather() — only offer the
            # AccuWeather follow-up when the fetch actually succeeded.
            weather_error_prefixes = (
                "My weather API key",
                "I couldn't find weather data",
                "I couldn't reach the weather service",
                "The weather request timed out",
                "I got a weather response but couldn't parse",
                "Something went wrong while fetching the weather",
            )
            weather_failed = result.startswith(weather_error_prefixes)

            if not weather_failed:
                speak("If you'd like, master, I can open up Ack-you-Weather to provide you with this entire week's forecast for Cebu City")
                while True:
                    confirmation = get_user_input()
                    if not confirmation or not confirmation.strip():
                        speak(get_empty_ack())   # Empty input — re-prompt
                        continue
                    if any(word in confirmation.lower() for word in affirm_triggers):
                        import webbrowser
                        speak(get_confirmation_ack())
                        webbrowser.open("https://www.accuweather.com/en/ph/cebu-city/264885/weather-forecast/264885")
                        speak("Displaying week-long forecast for Cebu City. Please standby...")
                        break
                    elif any(word in confirmation.lower() for word in decline_triggers):
                        speak("Well, alright then. What else can I do for you, Master?")
                        break
                    else:
                        speak("I didn't quite catch that, Master — yes or no?")  # Ambiguous — re-prompt
                        # No break — loop continues

            session_state.update(intent="weather", topic="Cebu City weather", expects_followup=False)
            return ""   # Return empty string so main.py skips the LLM but doesn't crash
    
        if intent == "news":
            result = get_news()
            if not result:
                return "Master, I can't seem to retrieve any headlines."
            speak(result)
            session_state.update(intent="news", topic="Cebu news", expects_followup=True)  #Smart intent classification of wanting more news
            speak("Want me to open a news page for the full story? I can pull up SunStar Cebu or Cebu Daily News.")
            while True:
                confirmation = get_user_input()
                if not confirmation or not confirmation.strip():
                    speak(get_empty_ack())   # Empty — re-prompt
                    continue
                text = confirmation.lower()
                if any(word in text for word in affirm_triggers):
                    import webbrowser
                    if "sunstar" in text or "sun star" in text:
                        speak(get_confirmation_ack())
                        webbrowser.open("https://www.sunstar.com.ph/cebu")
                        speak("Opening SunStar Cebu for you, Master")
                    elif "cdn" in text or "daily news" in text or "inquirer" in text:
                        speak(get_confirmation_ack())
                        webbrowser.open("https://cebudailynews.inquirer.net/")
                        speak("Opening Cebu Daily News for you, Master")
                    else:
                        speak(get_confirmation_ack())
                        webbrowser.open("https://www.sunstar.com.ph/cebu")  # Default to SunStar
                        speak("Opening SunStar Cebu for you, Master")
                    break
                elif any(word in text for word in decline_triggers):
                    speak("Well, alright then. What else can I do for you, Master?")
                    break
                else:
                    speak("I didn't quite catch that, Master — SunStar, Cebu Daily News, or no?")  # Ambiguous — re-prompt
                    # No break — loop continues

            return ""   # Same as above — skip LLM
        
        if intent == "news_search":
            topic = extract_news_topic(fairy_request)
            result = search_news(topic)
            speak(result)
            # Stay in news context so chained searches keep working
            session_state.update(intent="news", topic=topic, expects_followup=True)
            return ""
    
        if intent == "email":
            result = get_unread_emails()
            speak(result)
    
            # Only offer to mark as read if there were actually unread emails
            if "no unread" not in result.lower() and "problem" not in result.lower() and "couldn't" not in result.lower():
                speak("Should I mark those as read, Master?")
                confirmation = get_user_input()
                if confirmation and any(word in confirmation.lower() for word in affirm_triggers):
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
        
        if intent == "discord":
            result = get_recent_discord_messages()
            speak(result)
            return""

        if intent == "code":
            text = fairy_request.lower()
            path = extract_path(fairy_request)
    
            # ── Sub-routing: figure out WHICH code action is being requested ──
            if "comment" in text:
                if not path:
                    return "Which file should I comment, Master? Please give me the path."
                speak("Let me look that over, Master. This might take a moment.")
                summary, temp_path = generate_commented_version(path)
                speak(summary)
                if temp_path:
                    pending_comment_preview["filepath"] = path #take in the file path for the file
                    pending_comment_preview["temp_path"] = temp_path #same with a temporary path
                    confirmation = get_user_input()
                    #Key words for applying and discarding
                    apply_words = ["apply", "keep", "use it"] + affirm_triggers
                    discard_words = ["discard", "throw", "scrap"] + decline_triggers
                    #Variables to confirm command status (apply or discard)
                    is_apply = confirmation and any(w in confirmation.lower() for w in apply_words)
                    is_decline = confirmation and any(w in confirmation.lower() for w in discard_words)

                    #Detected Keywords to Apply
                    if is_apply and not is_decline:
                        speak(get_confirmation_ack()) #Confirm the command
                        result  = apply_commented_version(path, temp_path) #Apply the commented version at the relative path, and store 
                        speak(result)
                        #Reset the file paths
                        pending_comment_preview["filepath"] = None 
                        pending_comment_preview["temp_path"] = None 
                    #Detected Keywords to Discard
                    elif is_decline:
                        speak(get_decline_ack()) #Confirm the command
                        result  = discard_commented_version(temp_path) #Apply the commented version at the relative path, and store 
                        speak(result)
                        #Reset the file paths
                        pending_comment_preview["filepath"] = None 
                        pending_comment_preview["temp_path"] = None 
                    
                    else:
                        speak(f"I've left the preview as-is for now, Master. Say 'apply the comments' or 'discard the preview' when you're ready for '{os.path.basename(path)}'.")
                return ""
    
            if "commit" in text:
                # Path here is treated as the REPO folder, not a single file
                repo_path = path if path else fairy_request.split("at")[-1].strip() if "at" in text else None
                if not repo_path:
                    speak("Which repo should I generate a commit message for, Master? Please give me the path.")
                    reply = get_user_input() #Ask the user for which repo Fairy should target
                    repo_path = extract_path(reply) if reply else None
                    if not repo_path and reply and reply.strip():
                        repo_path = reply.strip().strip('"').strip("'")
                    if not repo_path:
                        return "I didn't catch a repo path there, Master. Let me know when you're ready." #Fallback in case Fairy doesn't detect the repository
                speak("Reading the diff, Master, one moment.")
                summary, draft_message, used_unstaged = generate_commit_message(repo_path)
                speak(summary)
                if draft_message:
                    confirmation = get_user_input()
                    if confirmation and any(w in confirmation.lower() for w in affirm_triggers):
                        speak(get_confirmation_ack())
                        result = confirm_commit(repo_path, draft_message, stage_first=used_unstaged)
                        speak(result)
                    else:
                        speak(get_decline_ack())
                        speak("Alright, I won't commit anything, Master.")
                return ""
    
            if any(w in text for w in ["diagnose", "debug", "fix this error", "error"]):
                if not path:
                    return "Which file is this error coming from, Master? Please give me the path."
                # Everything after the path mention is treated as the error message itself
                error_message = fairy_request
                speak("Let me take a look, Master.")
                result = diagnose_error(path, error_message)
                speak(result)
                return ""
    
            if "refactor" in text or "too long" in text:
                if not path:
                    return "Which file should I check, Master? Please give me the path."
                speak("Checking the structure, Master, one moment.")
                result = suggest_refactor(path)
                speak(result)
                return ""
    
            # Default: code review
            if not path:
                return "Which file should I review, Master? Please give me the path."
            speak("Reviewing now, Master. One moment.")
            result = review_code(path)
            speak(result)
            return ""
    
        if intent == "system":
            text = fairy_request.lower()
    
            # ── Sub-routing: figure out WHICH hardware action is being requested ──
            if "task manager" in text or "performance tab" in text:
                result = open_task_manager_performance()
                speak(result)
                return ""
    
            if any(w in text for w in ["security", "vulnerability", "secure", "port", "ports"]):
                speak("Running a quick security check, Master. One moment.")
                result = run_security_audit()
                speak(result)
                return ""
    
            if "clear" in text and ("cache" in text or "temp" in text):
                summary, temp_dir = preview_cache_clear()
                speak(summary)
                if "already clean" in summary.lower():
                    return ""
                confirmation = get_user_input()
                if confirmation and any(w in confirmation.lower() for w in affirm_triggers):
                    speak(get_confirmation_ack())
                    result = clear_cache(temp_dir)
                    speak(result)
                else:
                    speak(get_decline_ack())
                    speak("Leaving your temp cache as is, Master.")
                return ""
    
            if ("plot" in text or "graph" in text or "chart" in text) and ("performance" in text or "network" in text):
                speak("Sampling system performance over the next few seconds, Master. Please hold.")
                summary, _ = plot_performance_metrics()
                speak(summary)
                return ""
    
            # Default: spoken performance summary + battery threshold nag if applicable
            result = get_system_performance()
            speak(result)
            battery_warning = check_battery_threshold()
            if battery_warning:
                speak(battery_warning)
            return ""
        
            # AFTER
        if intent == "zzz":
            result = handle_zzz(fairy_request)
            speak(result)
            # Follow-up: if Fairy offered to open the notice, handle yes/no
            if "want me to open the full notice" in result.lower():
                follow = get_user_input()
                if follow and any(w in follow.lower() for w in affirm_triggers):
                    speak(get_confirmation_ack())
                    import webbrowser
                    webbrowser.open("https://zenless.hoyoverse.com/en-us/news")
                    speak("Opening the official Zenless page for events and notices, Master.")
                else:
                    speak("Alright, Master. Let me know if you need anything else.")
            return ""
        
        if intent == "sleep":
            result = handle_sleep_alarm(fairy_request)
            speak(result)
            return ""
        
        if intent == "reset":
            history.reset()
            session_state.reset()
            return "Memory cleared, Master. Starting fresh."
    
        # All other intents (chat, zzz, system, etc.) → fall through to LLM
        return None

    # Main loop
    conversation_active = False  # True once we've had at least one real exchange this "wake" cycle
    while True:
        if fairy_bridge.muted: #If muted
            time.sleep(0.2) #Small delay
            continue #Bypass and block out all voice input and continue as if nothing happened
        if conversation_active:
            # Listen directly for the next request; empty input here means "didn't catch that", not "waiting to be woken up".
            fairy_request = get_user_input()
            if not fairy_request:
                speak(get_empty_ack())
                conversation_active = False  # Drop back to standby after a missed turn
                continue
        else:
            inline_command = get_user_input(is_wakeword_check=True)  # Standby until wake word is detected
            if inline_command and inline_command.strip():
                # Command was already in the wake word sentence — use it directly
                fairy_request = inline_command
                print(f"[Inline command detected]: {fairy_request}")
            else:
                speak(get_wake_ack()) # Nothing after the wake word — listen for a separate request
                fairy_request = get_user_input()
                if not fairy_request:
                    speak(get_empty_ack())  # Wake word fired but nothing usable followed
                    continue

        if not fairy_request:
            continue #Carry on if nothing was heard

        conversation_active = True  # We got a real request — stay in conversation mode

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

            if followup and followup.strip() and classify_intent(followup, session_state) != "exit":
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