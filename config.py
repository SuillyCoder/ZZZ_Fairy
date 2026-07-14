#Load in the model for STT
from dotenv import load_dotenv
import os, sys

#Retrieving file paths relative to .exe program's actual loction
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

#Declare the base directory as a resuable instance
BASE_DIR = get_base_dir()

#Load in API keys from env file
load_dotenv(os.path.join(BASE_DIR, ".env"))

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
VOICE_MODEL_PATH = os.path.join(BASE_DIR, "voice_samples", "kokoro-v1.0.onnx")
VOICE_PACK_PATH = os.path.join(BASE_DIR, "voice_samples", "voices-v1.0.bin")
VOICE_VARIANT = "af_heart"
VOICE_SAMPLE_RATE = 24000 #24k Hz

# ===== VOSK settings ======
VOSK_MODEL_PATH = os.path.join(BASE_DIR, "vosk_model")

# ==== VAD Config Settings ====
SILENCE_THRESHOLD = 0.018  # Volume level below this = silence (raise if too sensitive)
SILENCE_DURATION = 1.5     # Seconds of silence before we assume you're done talking
CHUNK_SIZE = 512            # How many samples to read at a time (smaller = more responsive)
MAX_RECORDING_DURATION = 12  # Hard safety cap (seconds) — stops recording even if silence is never detected

#===== Audio DSP Filter Parameters ======
MIC_GAIN = 3.0           # Amplification multiplier — start at 3.0, tune from there
HIGHPASS_CUTOFF = 100    # Hz — removes rumble/hum below typical speech range

# ===== Ollama Settings=====S
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME  = "lfm2.5"  # Must match what you pulled in Ollama

# ===== GROQ Settings=====
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast + free tier
FAIRY_GROQ_API_KEY = os.getenv("FAIRY_GROQ_API_KEY")

# ======= API Keys ======== #
OWM_API_KEY = os.getenv("OWM_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ===== Google Cloud Services ==== #
GMAIL_TOKEN_PATH= os.path.join(BASE_DIR,'token.json')
GMAIL_CREDENTIALS_PATH =  os.path.join(BASE_DIR,'credentials.json')
SHEETS_TOKEN_PATH  =  os.path.join(BASE_DIR,"token_sheets.json")
EXPENSE_SHEET_ID   = os.getenv("EXPENSE_SHEET_ID")

# ======= API Keys ======== #
OWM_API_KEY = os.getenv("OWM_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ======== Discord APIs =========== #
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RAW_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
DISCORD_SERVER_ID = int(RAW_SERVER_ID) if RAW_SERVER_ID and RAW_SERVER_ID.isdigit() else None #Typecasting from string to integer

# ======== Hoyoverse Data ========== #
ZZZ_UID = os.getenv('ZZZ_UID')
HOYOLAB_LTUID = os.getenv('HOYOLAB_LTUID')
HOYOLAB_LTOKEN = os.getenv('HOYOLAB_LTOKEN')

# ========= Dataset Directories ======== #
DATASET_DIR = os.path.join(BASE_DIR, "computer_vision", "intruder_alert", "dataset")
VALIDATION_DIR = os.path.join(DATASET_DIR, "validation")
OUTPUT_PATH = os.path.join(
    BASE_DIR, "computer_vision", "intruder_alert", "reference_embeddings.pkl"
)
 
# ===== Transcription Settings =====
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "transcripts")
TRANSCRIPTION_SEGMENT_SECONDS = 8  # length of each chunk sent to Whisper; lower = snappier stop, more API calls