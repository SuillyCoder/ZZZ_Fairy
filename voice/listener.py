import sounddevice as sd #Importing sounddevice for mic access
import numpy as np #Importing numpy for necessary mathematical operations (or smth)
import time #for controlling delays in audio capture
import io, re, json
import soundfile as sf
from vosk import Model, KaldiRecognizer
from queue import Queue

#Adding the root to the search path when importing from other files
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#Imported variables from config.py
from config import SAMPLE_RATE, CHANNELS, WAKE_WORDS, NOISE_PATTERNS, CHUNK_SIZE, SILENCE_DURATION, SILENCE_THRESHOLD, FAIRY_GROQ_API_KEY, VOSK_MODEL_PATH, model, HIGHPASS_CUTOFF, MIC_GAIN, MAX_RECORDING_DURATION
#DSP filter function imports
from scipy.signal import butter, lfilter

#Model imports
from groq import Groq
if not FAIRY_GROQ_API_KEY:
    raise ValueError(
        "FAIRY_GROQ_API_KEY is missing or None. Check your .env file has "
        "a line like: FAIRY_GROQ_API_KEY=your_key_here (no quotes, no spaces around =)"
    )
groq_client = Groq(api_key=FAIRY_GROQ_API_KEY) #Groq model loading
vosk_model = Model(VOSK_MODEL_PATH) #Vosk model loading

def audio_filter(audio_chunk, gain=MIC_GAIN, cutoff=HIGHPASS_CUTOFF, sample_rate=SAMPLE_RATE):
    amplified = audio_chunk * gain #Amplifier Block: Vout = Vin * Av

    #High Pass Butterworth Filter (raw amplified audio is in; noise is thrown off)
    nyquist = sample_rate / 2
    normalized_cutoff = cutoff / nyquist
    b, a = butter(N=2, Wn=normalized_cutoff, btype='high')
    filtered = lfilter(b,a, amplified)

    #Safety clamp: prevent clipping above [-1, 1] after amplification ---
    filtered = np.clip(filtered, -1.0, 1.0)

    return filtered.astype(np.float32) #Filtered audiop gets returned as float32 data type format


def record_audio():

    audio_chunks = [] #initialize audio chunks array
    has_spoken = False  # True once we've detected at least one non-silent chunk
    last_sound_time = None  # Timestamp of the most recent confirmed (debounced) non-silent chunk
    loud_streak = 0  # Consecutive loud chunks seen in a row — used to debounce brief spikes
    LOUD_STREAK_NEEDED = 2  # Require 2 consecutive loud chunks (~32ms) before counting as real sound
    recording_done = False

    #Drain any audio already sitting in the mic buffer
    drain_duration = 0.3  # seconds to ignore at startup
    drain_chunks = int((SAMPLE_RATE / CHUNK_SIZE) * drain_duration)
    chunks_received = 0

    def callback(indata, frames, time_info, status):
        nonlocal recording_done, chunks_received, has_spoken, last_sound_time, loud_streak
        chunks_received += 1
        if chunks_received <= drain_chunks:
            return

        if recording_done:
            return #Dont process the audio until we've stopped
        chunk = indata.copy() #Set the chunk equal to data input (voice)
        chunk = audio_filter(chunk.flatten()).reshape(-1, 1) #Apply DSP filter
        audio_chunks.append(chunk) #add that chunk to the audio_chunk array
        volume = np.sqrt(np.mean(chunk **2)) #How loud is the chunk? (Measured after amplification)

        now = time.time()
        if volume >= SILENCE_THRESHOLD:
            loud_streak += 1
        else:
            loud_streak = 0
        # Debounce: only count this as real speech once we've seen several
        # loud chunks in a row. A single isolated spike (keyboard click,
        # breath, mic pop) won't pass this and won't reset the silence clock.
        if loud_streak >= LOUD_STREAK_NEEDED:
            has_spoken = True
            last_sound_time = now
        # Stop condition: once speech has started, stop after SILENCE_DURATION
        # seconds with no *confirmed* sound at all — measured by wall-clock
        # time elapsed since the last debounced loud chunk.
        if has_spoken and last_sound_time is not None and (now - last_sound_time) >= SILENCE_DURATION:
            recording_done = True

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='float32',
        blocksize=CHUNK_SIZE,
        callback=callback   # Called automatically for every chunk
    ):
        # Wait until the callback signals we're done, or until the hard
        # safety cap is hit — whichever comes first. The cap only matters
        # now if speech never stops (e.g. continuous background noise);
        # normal utterances stop on the SILENCE_DURATION condition above.
        start_time = time.time()
        while not recording_done:
            if time.time() - start_time > MAX_RECORDING_DURATION:
                print(f"[Recording] Hit {MAX_RECORDING_DURATION}s safety cap — stopping.")
                break
            time.sleep(0.05)

    if not audio_chunks:
        return np.array([], dtype='float32')

    return np.concatenate(audio_chunks, axis=0).flatten()


def transcribe_audio(audio_array): #Passes the 1D Array Sample as input parameter

    if audio_array is None or len(audio_array) == 0: #Checks if the audio array is empty to avoid unnecessary noise filler
        return ""
    
    #Convert float32 to WAV
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, SAMPLE_RATE, format='WAV')
    buffer.seek(0) 

    try:
        #create transcription via pre-loaded Groq model
        transcription = groq_client.audio.transcriptions.create(
            model= "whisper-large-v3",  # More accuracy, but a little slower (should be fine though)
            file=("audio.wav", buffer, "audio/wav"), #Save ass WAV file
            response_format="text",
            language = "en",
            prompt="The speaker is talking to an AI assistant named Fairy."
        )
        text = transcription.strip().lower()
        text = re.sub(r'[^\w\s]', '', text)  
        return text
    
    except Exception as e: #throw transcription error just in case
        print(f"[Transcription error]: {e}")
        return ""

SHORT_CONFIRMATION_WORDS = {
    "yes", "yeah", "yep", "sure", "please", "okay", "ok",
    "no", "nah", "nope",
}

def is_valid_transcription(text):
    if not text:
        return False
    stripped = text.strip()
    # Short yes/no replies are deliberate — let them through before the
    # length/repetition checks below, which would otherwise discard them.
    if stripped in SHORT_CONFIRMATION_WORDS:
        return True
    if len(stripped) < 3:
        return False
    if stripped in NOISE_PATTERNS:
        return False
    # Filter out single repeated words (another Whisper hallucination pattern)
    words = stripped.split()
    if len(words) <= 2 and len(set(words)) == 1:
        # e.g. "the the" or "um" — likely noise
        return False
    return True

def listen_for_wakeword():
    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)
    recognizer.SetWords(True)
    q = Queue()

    def callback(indata, frames, time_info, status):
        chunk = audio_filter(indata.flatten()).reshape(-1, 1)
        audio_bytes = (chunk * 32767).astype(np.int16).tobytes() #Convert the audio into int16 from float32 via typecasting
        if recognizer.AcceptWaveform(audio_bytes): #If the waveform is acceptable 
            result = json.loads(recognizer.Result()) #Load the result as parsed json
            text = result.get("text", "").strip().lower() #pass those results as the full stream of text
            if text:
                q.put(text) #Add the stream of text into the queue

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,dtype='float32', blocksize=CHUNK_SIZE, callback=callback):
        while True:
            text = q.get(block=True, timeout=None)  # Blocks until Vosk produces a finalized phrase
            print(f"[Fairy heard]: {text}")

            for wake_word in WAKE_WORDS:
                if wake_word in text:
                    snippet_remains = text.split(wake_word, 1)[-1].strip()
                    return snippet_remains
        
def listen_for_request():
    print("Awaiting your request...")
    time.sleep(0.3)

    audio = record_audio() #Give it some time to record audio commands
    fairy_request = transcribe_audio(audio) #Break down the audio command into text
    
    if not is_valid_transcription(fairy_request):
        print(f"[Invalid input ignored]: '{fairy_request}'")
        return ""
    
    print(f"Request received: {fairy_request}")
    return fairy_request