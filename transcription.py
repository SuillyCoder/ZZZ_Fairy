#Import dependencies
import os, time, threading
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundcard as sc
from groq import Groq
from pynput import keyboard

from gui.bridge import fairy_bridge

#Import the necessary config files
from config import(
    SAMPLE_RATE, CHANNELS, FAIRY_GROQ_API_KEY,
    TRANSCRIPTS_DIR, TRANSCRIPTION_SEGMENT_SECONDS, NOISE_PATTERNS,
)

#Import resonses
from brain.responses import get_confirmation_ack

#Hotkey imports
from gui.hotkeys import (
    set_transcription_stop_event,
    start_end_transcription_listener,
    stop_end_transcription_listener,
)

#Instantiate the groq client
groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="soundcard")

# === Capture ==== #

def record_segment_in_device(seconds: int) -> np.ndarray:
    speaker = sc.default_speaker() #Acquire the default speaker
    loopback_mic = sc.get_microphone(speaker.name, include_loopback=True)#Enable loopback
    chunk_frames = int(SAMPLE_RATE * 0.5)  # read in half-second increments to avoid buffer overrun
    total_frames_needed = int(SAMPLE_RATE * seconds)
    collected, frames_collected = [], 0

    with loopback_mic.recorder(samplerate=SAMPLE_RATE, channels=CHANNELS) as rec:
        while frames_collected < total_frames_needed:
            if _stop_event.is_set():
                break
            data = rec.record(numframes=int(seconds * SAMPLE_RATE))
            collected.append(data)
            frames_collected += data.shape[0]

    if not collected:
        return np.array([], dtype='float32')
    return np.concatenate(collected, axis=0).flatten()

def record_segment_external(seconds: int) -> np.ndarray:
    chunk_frames = int(SAMPLE_RATE * 0.5)
    total_frames_needed = int(SAMPLE_RATE * seconds)
    collected, frames_collected = [], 0

    while frames_collected < total_frames_needed:
        if _stop_event.is_set():
            break
        data = sd.rec(chunk_frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32')
        sd.wait()
        collected.append(data)
        frames_collected += data.shape[0]

    if not collected:
        return np.array([], dtype='float32')
    return np.concatenate(collected, axis=0).flatten()


# ====== Transcription Process ===== #

def transcribe_segment(audio_array: np.ndarray) -> str:
    if audio_array is None or len(audio_array) == 0:
        return ""
    import io, soundfile as sf
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, SAMPLE_RATE, format='WAV')
    buffer.seek(0)

    try:
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=("segment.wav", buffer, "audio/wav"),
            response_format="text",
            language="en",
        )
        text = transcription.strip()
        if not text or text.lower().rstrip(".") in NOISE_PATTERNS:
            return ""
        return text
    except Exception as e:
        print(f"[Transcription Error]: {e}")
        return ""

# ==== Export ==== #
def export_transcript(lines: list[str], as_pdf: bool) -> str:
    os.makedirs(TRANSCRIPTS_DIR, exist_ok = True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if as_pdf:
        from fpdf import FPDF
        path = os.path.join(TRANSCRIPTS_DIR, f"transcript_{stamp}.pdf")
        pdf = FPDF
        pdf.add_page()
        pdf.set_font('Helvetica', size=11)
        for line in lines:
            pdf.multi_cell(0,8,line)
        pdf.output(path)
    else:
        path = os.path.join(TRANSCRIPTS_DIR, f"transcript_{stamp}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) if lines else "(No speech detected.)")
    return path

# ==== Public Entry Point === #

def run_transcription_session(fairy_request: str, speak_fn, get_input_fn) -> str:
    global _stop_event
    _stop_event = threading.Event()
    set_transcription_stop_event(_stop_event)

    as_pdf = "pdf" in fairy_request.lower()

    #Ask which capture method should be done
    speak_fn(get_confirmation_ack())
    speak_fn("Should I transcribe outside audio, or in-device audio, Master?")
    mode = None #Set the current mode to an unchosen one

    while mode is None: 
        answer = get_input_fn()
        if not answer or not answer.strip():
            speak_fn("I didn't catch that, Master — outside, or in-device?")
            continue
        answer_lower =answer.lower()
        if any(w in answer_lower for w in ["outside", "external", "mic", "microphone", "in person", "in-person"]):
            mode = "external"
        elif any(w in answer_lower for w in ["in-device", "in device", "internal", "system audio", "device audio", "inside"]):
            mode = "in-device"
        else:
            speak_fn("Sorry, Master — outside audio, or in-device audio?")
        
    start_end_transcription_listener()
    speak_fn(f"Starting {mode} transcription, Master.")
    print(f"[Transcription] Session started — mode: {mode}, segment length: {TRANSCRIPTION_SEGMENT_SECONDS}s")

    if mode == "in-device":
        was_muted = fairy_bridge.muted
        fairy_bridge.muted = True  # Silence Fairy's own voice so it doesn't bleed into the loopback capture
        
    transcript_lines = []
    try: 
        while not _stop_event.is_set():
            timestamp = datetime.now().strftime("%H:%M:%S")
            audio = (
                record_segment_in_device(TRANSCRIPTION_SEGMENT_SECONDS)
                if mode == "in-device"
                else record_segment_external(TRANSCRIPTION_SEGMENT_SECONDS)
            )
            if _stop_event.is_set():
                break
            text = transcribe_segment(audio)
            if text:
                transcript_lines.append(f"[{timestamp}] {text}")
                print(f"[Transcription] {timestamp}: {text}")
    finally:
        stop_end_transcription_listener()
        if mode == "in-device":
            fairy_bridge.muted = was_muted # Restore whatever the mute state was before this session

    filepath = export_transcript(transcript_lines, as_pdf)
    return f"Transcription ended, Master. Saved {len(transcript_lines)} segment(s) to '{filepath}'."