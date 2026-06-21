#Importing the model here instead
from dotenv import load_dotenv
import whisper, os

#Load in API keys from env file
load_dotenv()

#Load in the model for STT
from dotenv import load_dotenv
import whisper, os

#Load in API keys from env file
load_dotenv()

#Load in the model for STT
model = whisper.load_model("base") #Base Model

#Load in the project root 
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

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
WAKE_WORDS = ["hey fairy", "fairy", "yo fairy", "hello fairy", "ferry", "mary", "very", "faery", "faire", "harry", "fary"]

# ===== Piper TTS Settings =====
VOICE_MODEL_PATH = "voice_samples/kokoro-v1.0.onnx"
VOICE_PACK_PATH = "voice_samples/voices-v1.0.bin"
VOICE_VARIANT = "af_heart"
VOICE_SAMPLE_RATE = 24000 #24k Hz

# ===== VOSK settings ======
VOSK_MODEL_PATH = "vosk_model"

# ==== VAD Config Settings ====
SILENCE_THRESHOLD = 0.01   # Volume level below this = silence (raise if too sensitive)
SILENCE_DURATION = 0.7     # Seconds of silence before we assume you're done talking
CHUNK_SIZE = 512            # How many samples to read at a time (smaller = more responsive)

# ===== Ollama Settings=====
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME  = "lfm2.5"  # Must match what you pulled in Ollama

# ===== GROQ Settings=====
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast + free tier
FAIRY_GROQ_API_KEY = os.getenv("FAIRY_GROQ_API_KEY")

# ======= API Keys ======== #
OWM_API_KEY = os.getenv("OWM_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ===== Google Cloud Services ==== #
GMAIL_TOKEN_PATH= os.path.join(PROJECT_ROOT,'token.json')
GMAIL_CREDENTIALS_PATH =  os.path.join(PROJECT_ROOT,'credentials.json')
SHEETS_TOKEN_PATH  =  os.path.join(PROJECT_ROOT,"token_sheets.json")
EXPENSE_SHEET_ID   = os.getenv("EXPENSE_SHEET_ID")

# ======= API Keys ======== #
OWM_API_KEY = os.getenv("OWM_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ======== Discord APIs =========== #
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RAW_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
DISCORD_SERVER_ID = int(RAW_SERVER_ID) if RAW_SERVER_ID.isdigit() else None #Typecasting from string to integer