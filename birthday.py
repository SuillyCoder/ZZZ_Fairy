from config import BASE_DIR
import datetime, os, subprocess, threading, time
from voice.speaker import speak

#Import the path for the birthday video
BIRTHDAY_VIDEO_PATH = os.path.join(BASE_DIR, "media", "Zenless_Birthday.mp4")

def happy_birthday():
    #Get the current date via date time
    current_date = datetime.datetime.now() 
    month = current_date.month
    day = current_date.day
    year = current_date.year

    # ======== VIDEO PLAYING ROUTINE ======== #
    if month == 1 and day == 26:
        speak(f"Master, I've checked today's date. It's January 26, {year}. You know exactly what day it is today.")
        if os.path.exists(BIRTHDAY_VIDEO_PATH):
            os.startfile(BIRTHDAY_VIDEO_PATH)  # hands off to Windows' default video player
            time.sleep(20)
            speak("A big Happy Birthday to you, Master! Thank you for having me around to celebrate it with you! I hope you have a great day! Now, on to business...")

