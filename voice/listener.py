import sounddevice as sd #Importing sounddevice for mic access
import numpy as np #Importing numpy for necessary mathematical operations (or smth)
import time #for controlling delays in audio capture

#Adding the root to the search path when importing from other files
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#Imported variables from config.py
from config import SAMPLE_RATE, CHANNELS, WAKE_WORDS, NOISE_PATTERNS, CHUNK_SIZE, SILENCE_DURATION, SILENCE_THRESHOLD, FAIRY_GROQ_API_KEY

#Groq import
from groq import Groq
groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

def record_audio():
    audio_chunks = [] #initialize audio chunks array
    silent_chunks = 0 #chunks for dead air

    # How many silent chunks = SILENCE_DURATION seconds of silence
    chunks_for_silence = int((SAMPLE_RATE / CHUNK_SIZE) * SILENCE_DURATION)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32') as stream:
        while True:
            chunk, _ = stream.read(CHUNK_SIZE)
            audio_chunks.append(chunk.copy())

            # Calculate volume (RMS) of this chunk
            volume = np.sqrt(np.mean(chunk ** 2))

            if volume < SILENCE_THRESHOLD:
                silent_chunks += 1
            else:
                silent_chunks = 0  # Reset silence counter if sound detected

            # Stop recording once enough silence has passed
            if silent_chunks >= chunks_for_silence and len(audio_chunks) > chunks_for_silence:
                break

    # Flatten all chunks into one array
    return np.concatenate(audio_chunks, axis=0).flatten()

def transcribe_audio(audio_array): #Passes the 1D Array Sample as input parameter
    import io
    import soundfile as sf

    buffer = io.BytesIO()
    sf.write(buffer, audio_array, SAMPLE_RATE, format='WAV')
    buffer.seek(0) 

    #create transcription via pre-loaded Groq model
    transcription = groq_client.audio.transcriptions.create(
        model="whisper-large-v3",  # More accuracy, but a little slower (should be fine though)
        file=("audio.wav", buffer, "audio/wav"),
        response_format="text"
    )

    return transcription.strip().lower()

def is_valid_transcription(text):
    """Returns False if the transcription looks like noise or silence."""
    if len(text) < 3:  # Too short to be a real command
        return False
    if text in NOISE_PATTERNS:
        return False
    return True

def listen_for_wakeword():
    print("On standby....")
    time.sleep(1)

    while True:
        #Passing recorded audio and transcribed audio as variables
        audio = record_audio() 
        text = transcribe_audio(audio)
        print(f"Heard: {text}")  # <-- add this so you can see what's being transcribed

        if not is_valid_transcription(text):
            continue

        for wake_word in WAKE_WORDS: #Checks for all the wakewords present in text
            if wake_word in text: #If the wakeword is found...
                snippet_remains = text.split(wake_word, 1)[-1].strip() #Extract the remaining text
                return snippet_remains #Return the rest of the text
        
def listen_for_request():
    print("Awaiting your request...")
    audio = record_audio() #Give it some time to record audio commands
    fairy_request = transcribe_audio(audio) #Break down the audio command into text
    print(f"Request received: {fairy_request}")
    return fairy_request