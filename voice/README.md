# Voice Pipeline

This is Fairy's "ears and mouth" — the layer responsible for detecting when you're talking to her, turning your speech into text, and turning her replies back into spoken audio.

The pipeline runs in three stages: **wake word detection → speech-to-text → text-to-speech**. The first two stages happen in `listener.py`; the third lives in `speaker.py`.

## Wake word detection — `listen_for_wakeword()`

Runs continuously in the background, listening for a wake phrase (e.g. "Fairy") using **Vosk**, an offline speech recognizer. Because it's fully offline, this stage runs with zero API cost or latency — important since it's always-on.

- Streams microphone audio through a custom DSP filter (gain + high-pass Butterworth filter via `scipy.signal`) to clean up background noise before Vosk ever sees it
- Once Vosk finalizes a phrase, checks it against a configurable wake-word list
- Returns whatever was said *after* the wake word, so a single utterance like "Fairy, what's the weather" can skip straight to processing the request

**Tools/libraries:** `vosk`, `sounddevice`, `scipy.signal`, `numpy`

## Speech-to-text — `record_audio()` + `transcribe_audio()`

Once woken, Fairy records your actual request and sends it to **Groq's Whisper (`whisper-large-v3`)** for transcription.

- `record_audio()` uses a silence-detection callback to know when you've stopped talking — no fixed recording length, no "press enter when done"
- Includes a short buffer-drain step at the start to discard stale audio sitting in the mic buffer
- `transcribe_audio()` converts the recorded array to WAV in-memory and sends it to Groq's Whisper endpoint, with a custom prompt hint ("the speaker is talking to an AI assistant named Fairy") to bias transcription accuracy
- `is_valid_transcription()` filters out Whisper hallucination patterns — empty results, repeated single words, and known noise phrases — so silence or static doesn't get treated as a real command

**Tools/libraries:** `groq` (Whisper API), `soundfile`, `numpy`, `sounddevice`

## Text-to-speech — `speak()`

Converts Fairy's text replies into audio using **Kokoro ONNX**, a lightweight local TTS model — then applies a custom effect to make it sound less like a generic voice assistant and more like an in-game AI.

- Loads a specific Kokoro voice variant and pack at startup
- `apply_robot_ripple()` applies an amplitude-modulated sine wave over the generated audio — a custom DSP effect (not part of Kokoro) that gives the voice a subtle robotic "ripple," tunable via `ripple_rate` and `ripple_depth`
- Plays the result directly through the system's audio output via `sounddevice`

**Tools/libraries:** `kokoro_onnx`, `sounddevice`, `scipy.signal`, `numpy`

## Current scope

| Capability | Status |
|---|---|
| Offline wake word detection | ✅ |
| Noise-filtered audio capture | ✅ |
| Cloud-based transcription (Whisper via Groq) | ✅ |
| Local TTS with custom robotic effect | ✅ |
| Fully offline STT/TTS (no cloud dependency) | 🔲 Not yet — Whisper transcription requires Groq API access |
