# ZZZ_Fairy

<p>A local, voice-first AI assistant for Windows — inspired by **Fairy**, the AI companion from *Zenless Zone Zero*. Fairy listens for a wake word, transcribes your voice, classifies what you want, and routes the request to the right module: live weather and news, Gmail and Discord checks, expense analysis, code review, device/security monitoring, and Zenless Zone Zero account tracking — all spoken back in character.</p>

# Project Origin

<p align="center">
<img width="686" height="386" alt="image" src="https://github.com/user-attachments/assets/024b6b6c-ad01-43fc-bffe-aa86edaa6874" />
<p align="center">
<p>AI, automation, and LLM orchestration are some of the fastest-moving areas in tech right now. Rather than just reading about agentic workflows, multi-model orchestration, and system-level concepts (concurrency, security, web scraping), this project is a hands-on way to actually build them — while making something genuinely useful to run on my own machine every day. </p>

<p align="center">
<img width="616" height="353" alt="image" src="https://github.com/user-attachments/assets/28561bd5-74a1-42eb-8aa8-c63908ca7b84" />
<p align="center">
<p>On a random note, there's a game that I really like: Zenless Zone Zero. It's one of the gacha games that I've stuck around with for the longest time, and still find time to play every now and then. </p>

# Project Idea
<p align="center">
<img width="867" height="538" alt="image" src="https://github.com/user-attachments/assets/e4392393-9f9c-47dd-8d90-2c0291ce8a36" />
<p align="center">
<p>There's a character named Fairy in *Zenless Zone Zero* — the in-universe AI assistant who helps the protagonists with everything from menial tasks to high-stakes operations, think Jarvis, but for a gacha game I've sunk a lot of hours into. Combining a game I like with a skill set I wanted to build felt like the obvious move: a portfolio project with a personality, not just another to-do list app.</p>

## What Fairy can do

| Module | Folder | Covers |
|---|---|---|
| **Voice Pipeline** | [`voice/`](voice/README.md) | Wake word detection, speech-to-text, text-to-speech with a custom robotic voice filter |
| **Brain / Orchestration** | [`brain/`](brain/README.md) | Intent classification, conversation memory, persona, session follow-ups |
| **Web Info** | [`api/`](api/README.md) | Live weather and local news (API + scraper fallback) |
| **Automation** | [`automation/`](automation/README.md) | Gmail, Discord, expense tracking, AI-assisted code review |
| **Device Control** | [`device/`](device/README.md) | CPU/RAM/battery monitoring, cache clearing, security audits, performance plotting |
| **Computer Vision** | [`computer_vision/`](computer_vision/README.md) | Sleep alarm (drowsiness detection) and intruder alert (face recognition + device lock) |
| **Entertainment** | [`entertainment/`](entertainment/README.md) | Spotify music control, Netflix/streaming launcher, Steam game recommendations |
| **Zenless Zone Zero** | [`zenless/`](zenless/README.md) | Account status, character showcase, banners, news — for the game itself |

## Model orchestration at a glance
 
```
Groq (llama-3.1-8b-instant)    → persona, conversation, intent-adjacent language tasks
Ollama (lfm2.5, local)          → heavy/data-crunching tasks (code review, financial analysis)
Vosk                            → offline wake-word detection
Groq Whisper (whisper-large-v3) → speech-to-text after wake word
Kokoro ONNX                     → text-to-speech, with a custom amplitude-modulated "robot ripple" effect
facenet-pytorch (InceptionResnetV1, VGGFace2) → face identity matching for Intruder Alert
MediaPipe FaceLandmarker        → eye landmark extraction for Sleep Alarm
```

## Tech stack

Python 3.12 · Groq API · Ollama · Vosk · Kokoro ONNX · Gmail API · Google Sheets (`gspread`) · `discord.py` · Enka.Network · `genshin.py` (HoYoLAB) · Ennead API · `psutil` · `matplotlib` · `BeautifulSoup` · `spotipy` (Spotify) · Steam Web API · `facenet-pytorch` · `mediapipe` · OpenCV · `pygame`

---

## Application Interface

<img width="1907" height="1097" alt="image" src="https://github.com/user-attachments/assets/18f58bd2-1170-43b6-8728-276d4060dd57" />
</br>

The program is run and presented via a simple terminal interface, accompanied by Fairy's ever-spinning icon, to get an immersive feel of Fairy's presence (like in the game), as well as have easier logging and output viewing. As of writing this, I'm not gonna lie: it feels pretty good being able to make this little project. Of course, I'm far from done. I have loads of other things planned, as well as some other things to polish up. Until then, this project is gonna be fun. 

---



