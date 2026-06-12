#Importing the model here instead
import whisper
model = whisper.load_model("base") #Base Model

#==Configuring audio settings==#
SAMPLE_RATE = 16000 #Constant frequency value (16KHz) for Whisper to operate
DURATION = 5 #Seconds to record per chunk
CHANNELS = 1 #Mono Audio

#==Wake Words==#
WAKE_WORDS  = ["hey fairy", "fairy", "yo fairy", "hello fairy"]

# ===== Piper TTS Settings =====
VOICE_MODEL_PATH = "voice_samples/en_US-libritts_r-medium.onnx"
VOICE_CONFIG_PATH = "voice_samples/en_US-libritts_r-medium.onnx.json"
VOICE_SAMPLE_RATE = 22050

# ===== Ollama Settings (for Phase 3) =====
OLLAMA_MODEL = "llama3.2"  # Update this to whatever model you pulled

