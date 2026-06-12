import sounddevice as sd #Importing sounddevice for mic access
import numpy as np #Importing numpy for necessary mathematical operations (or smth)

#Adding the root to the search path when importing from other files
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#Imported variables from config.py
from config import model, SAMPLE_RATE, DURATION, CHANNELS, WAKE_WORDS

def record_audio(duration=DURATION):
    #Active recording of user voice input
    audio = sd.rec(
        int(duration * SAMPLE_RATE),  # Total number of samples to record
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='float32'
    )

    sd.wait() #Wait to finish recording
    return audio.flatten() #Returns audio samples as a 1 D array

def transcribe_audio(audio_array): #Passes the 1D Array Sample as input parameter
    result  = model.transcribe(audio_array) #Pass in the actual recorded audio\
    return result["text"].strip().lower() #Split the entire sentence input into worded chunks

def listen_for_wakeword():
    print("On standby....")

    while True:
        #Passing recorded audio and transcribed audio as variables
        audio = record_audio() 
        text = transcribe_audio(audio)
        print(f"Heard: {text}")  # <-- add this so you can see what's being transcribed

        if any(wake_word in text for wake_word in WAKE_WORDS):
            return True
        
def listen_for_request():
    print("Awaiting your request...")
    audio = record_audio(duration=5) #Give it some time to record audio commands
    fairy_request = transcribe_audio(audio) #Break down the audio command into text
    print(f"Request received: {fairy_request}")
    return fairy_request