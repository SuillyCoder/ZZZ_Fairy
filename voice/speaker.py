from kokoro_onnx import Kokoro
import sounddevice as sd
import numpy as np
from scipy import signal
import threading
speak_lock = threading.Lock() #Add a thread blocker to handle multiple speaking instances

#Adding the root to the search path when importing from other files
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOICE_MODEL_PATH, VOICE_PACK_PATH, VOICE_VARIANT

# == Set values for voice rippling
ripple_rate = 50
ripple_depth = 0.3

#Load in the chosen voice
kokoro = Kokoro(VOICE_MODEL_PATH, VOICE_PACK_PATH)

#Ripply effect for voice sample
def apply_robot_ripple(audio: np.ndarray, sample_rate: int, ripple_rate, ripple_depth) -> np.ndarray:
    t = np.arange(len(audio)) / sample_rate
    modulator = 1 - ripple_depth + ripple_depth * np.sin(2 * np.pi * ripple_rate * t) #Simple sine oscillator
    rippled = audio * modulator #Forced rippled response on the audio
    
    max_val = np.max(np.abs(rippled))
    if max_val > 0:
        rippled = rippled / max_val * np.max(np.abs(audio))

    return rippled.astype(np.float32) #Return the rippled audio as a float32 data type (since that's what Kokoro accepts)

#Function for Fairy to speak
def speak(text :str):
    with speak_lock: #Only one spoken phrase at a time. Prevents thread overlap
        print(f"Fairy says: {text}")

        #A guard to check if text has actually been administered
        if not text or not text.strip:   
            print("[Speaker]: Nothing to say — empty response received.")
            return
    
        samples, sample_rate = kokoro.create(
            text,
            voice = VOICE_VARIANT,
            speed = 1.0,
            lang = "en-us"
        )

        if samples is None or len(samples) == 0: #Empty sample generation
            print("[Speaker]: Kokoro returned no audio.")
            return

        rippled_audio = apply_robot_ripple(samples, sample_rate, ripple_rate, ripple_depth)
    
        sd.play(rippled_audio, samplerate=sample_rate) #Play the audio based on the given sample rate
        sd.wait() #Wait for it to finish



