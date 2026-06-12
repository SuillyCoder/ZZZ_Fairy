from piper.voice import PiperVoice #Importing the voice libraries
import wave
import sounddevice as sd
import numpy as np

#Adding the root to the search path when importing from other files
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOICE_CONFIG_PATH, VOICE_MODEL_PATH, SAMPLE_RATE

#Load in the chosen voice
voice = PiperVoice.load(VOICE_MODEL_PATH, config_path=VOICE_CONFIG_PATH,)

#Function for Fairy to speak
def speak(text :str):
    print(f"Fairy says: {text}")
    audio_chunks = [] #All the audio broken down into textual chunks

    #synthesize() function yields audio chunks and processes them as text
    for audio_chunk in voice.synthesize(text):
        audio_chunks.append(audio_chunk.audio_int16_array) #Store all the the audio chunks into int16 audio array

    audio_array = np.concatenate(audio_chunks) #String all the chunks together
    audio_float = audio_array.astype(np.float32) / 32768.0 #Conversion from int16 PCM top float32 for sounddevice to play it
 
    sd.play(audio_float, samplerate=voice.config.sample_rate) #Play the audio based on the given sample rate
    sd.wait() #Wait for it to finish



