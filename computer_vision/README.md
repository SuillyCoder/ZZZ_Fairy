# Computer Vision

Two camera-based features that give Fairy awareness of what's physically happening at the machine. Both share a single webcam through a **mutual exclusion layer** (`cv_state.py`) — only one can hold the camera at a time, and activating one forcefully stops the other before starting.

## Shared camera arbitration — `cv_state.py`

A lightweight threading lock with two operations:
- `activate(feature_name, stop_fn)` — claims the camera for a feature; if another feature already holds it, calls that feature's `stop_fn` first to cleanly release it
- `deactivate(feature_name)` — releases the claim when a feature stops

This prevents two detection loops from fighting over the same hardware resource, or one crashing because the other already opened `cv2.VideoCapture(0)`.

**Tools/libraries:** `threading` (standard library)

---

## Sleep Alarm — `sleep_alarm/`

Monitors the user's eyes via webcam and sounds an alarm if they've been closed for 5+ seconds — a drowsiness/falling-asleep-at-desk detector, repurposed and integrated into Fairy from a prior standalone project (SleeperBeeper).

### How it works

**Face detection → landmark extraction → EAR calculation → alarm trigger**

1. **Haar cascade** (`haarcascade_frontalface_default.xml`) detects faces in each frame — fast, CPU-friendly, no GPU required
2. **MediaPipe FaceLandmarker** (`.task` model file) extracts precise per-frame face landmarks from the detected face region
3. **Eye Aspect Ratio (EAR)** is calculated for both eyes using 6 landmark points per eye via the Euclidean-distance formula — a ratio that approaches zero as eyes close
4. If EAR drops below `0.18` for 5+ consecutive seconds, the alarm sound fires via `pygame`
5. As soon as eyes open, `pygame.mixer.stop()` silences the alarm and the timer resets
6. After 3 alarm-blare cycles without the user responding, Fairy speaks a banter line via the TTS pipeline — escalating the wake-up call

The camera loop runs on a daemon thread so the main program stays responsive. A `stop()` method cleanly releases the camera, stops audio, and closes the OpenCV window — called by `cv_state` when Intruder Alert takes over, or by the user pressing `q`.

**Tools/libraries:** `opencv-python` (`cv2`), `mediapipe`, `scipy.spatial.distance`, `pygame`, `PIL`

---

## Intruder Alert — `intruder_alert/`

A real-time face recognition security monitor — watches the webcam, identifies who's in frame, and triggers an alarm + workstation lock if an unauthorized person gets too close for too long.

### How it works

**Face detection → identity matching → proximity + time thresholds → alarm/lock**

#### Reference embedding setup (one-time, offline)
`build_reference_embeddings.py` runs **offline** to pre-enroll known identities. It:
1. Reads a folder of reference photos per identity (e.g. `enzo/`, `rafiq/`)
2. Crops each face with **MTCNN** (Multi-task Cascaded Convolutional Network) — the standard face-detection stage before FaceNet-style models
3. Embeds each crop with **InceptionResnetV1** pretrained on VGGFace2 — a 512-dimensional face embedding vector
4. Saves all embeddings to `reference_embeddings.pkl`

#### Live detection (`FaceMatcher` + `IntruderAlertCamera`)
Per frame:
1. **Haar cascade** detects faces (fast, runs every frame)
2. Every 0.3s, the most prominent face is passed to `FaceMatcher.identity()` — MTCNN crops it, InceptionResnetV1 embeds it, and it's compared to all stored reference embeddings via **Euclidean distance**. Closest match below `MATCH_THRESHOLD=0.9` wins; above the threshold → `"unknown"`

#### State machine and response logic
- **Enzo (owner) detected:** disarms any pending alarm state; if returning after a confirmed absence (60s+ away), Fairy greets the return and reports what happened
- **Rafiq or unknown detected close-up** (`face_area ≥ 45,000 px²` for 7+ continuous seconds): triggers alarm sound, minimizes all windows (`Shell.Application.MinimizeAll()`), and locks the workstation (`ctypes.windll.user32.LockWorkStation()`)
- A pending Fairy warning speech fires *after* the alarm sound finishes (to avoid audio overlap with the TTS pipeline) — same audio-sequencing pattern used in Sleep Alarm

Identity label and face bounding box are overlaid on the live OpenCV window so you can see what the system is reading in real time.

**Tools/libraries:** `facenet-pytorch` (MTCNN, InceptionResnetV1), `opencv-python` (`cv2`), `torch`, `pygame`, `PIL`, `ctypes`, `subprocess` (PowerShell)

---

## Current scope

| Capability | Status |
|---|---|
| EAR-based drowsiness detection + alarm | ✅ |
| Fairy banter escalation on repeated sleep triggers | ✅ |
| Face recognition with pre-enrolled identities | ✅ |
| Proximity + time-threshold alarm and device lock | ✅ |
| Owner return detection + absence-aware reporting | ✅ |
| Mutual exclusion between Sleep Alarm and Intruder Alert | ✅ |
| Enrolling new identities via voice command (no manual script run) | 🔲 Not yet — enrollment requires running `build_reference_embeddings.py` manually |
| Multi-camera support | 🔲 Not yet — hardcoded to `cv2.VideoCapture(0)` |
