#Importing the model here instead
import whisper
model = whisper.load_model("base") #Base Model

#==Configuring audio settings==#
SAMPLE_RATE = 16000 #Constant frequency value (16KHz) for Whisper to operate
DURATION = 5 #Seconds to record per chunk
CHANNELS = 1 #Mono Audio

# A basic noise/silence filter
NOISE_PATTERNS = [
    # Whisper silence hallucinations
    "thank you", "thanks", "you're welcome", "thanks for watching",
    "thank you for watching", "bye", "goodbye", "mary", "very",
    ".", "..", "...", " ", "",
]

#==Wake Words==#
WAKE_WORDS  = ["hey fairy", "fairy", "yo fairy", "hello fairy", "ferry", "mary", "very", "faery", "faire"]

# ===== Piper TTS Settings =====
VOICE_MODEL_PATH = "voice_samples/en_US-libritts_r-medium.onnx"
VOICE_CONFIG_PATH = "voice_samples/en_US-libritts_r-medium.onnx.json"
VOICE_SAMPLE_RATE = 22050

# ==== VAD Config Settings ====
SILENCE_THRESHOLD = 0.01   # Volume level below this = silence (raise if too sensitive)
SILENCE_DURATION = 0.7     # Seconds of silence before we assume you're done talking
CHUNK_SIZE = 512            # How many samples to read at a time (smaller = more responsive)

# ===== Ollama Settings=====
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME  = "lfm2.5"  # Must match what you pulled in Ollama

# ===== GROQ Settings=====
FAIRY_GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast + free tier
