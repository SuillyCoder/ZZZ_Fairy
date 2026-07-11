#Camera setup file

#All the necessary imports
import ctypes, os, subprocess, threading, time, cv2, pygame
from PIL import Image
from config import BASE_DIR
from voice.speaker import speak
from computer_vision.intruder_alert.face_matcher import FaceMatcher
from brain.responses import get_red_handed_ack

def resource_path(relative_path):
    return os.path.join(BASE_DIR, "computer_vision", "intruder_alert", relative_path)
 
 
# ── Tunable thresholds (from the Intruder Alert flowchart) ──
RECOGNITION_INTERVAL_SECONDS = 0.3  # how often to run the heavier TBNN identity check
PROXIMITY_AREA_THRESHOLD = 45000   # Haar box (w*h) considered "near the laptop"; tune to your webcam
PROXIMITY_HOLD_SECONDS = 7.0       # how long Rafiq/Unknown must stay close before alarming
AWAY_CONFIRM_SECONDS = 60.0          # elapsed absence before treating it as a real departure
RETURN_CONFIRM_SECONDS = 5.0         # elapsed presence before treating a return as real

def _minimize_all_windows(): #Minimize all active windows upon detection 
    subprocess.run([
        "powershell", "-NoProfile", "-Command",
         "(New-Object -ComObject Shell.Application).MinimizeAll()"],
         capture_output = True
    )

def _lock_workstation(): #Lock the device as soon as it finds Rafiq in the frame
    ctypes.windll.user32.LockWorkStation() #Powershell command for device locking


class IntruderAlertCamera: 
    def __init__(self, matcher, on_stop_callback=None):
        self.face_cascade = cv2.CascadeClassifier(resource_path('haarcascade_frontalface_default.xml')) #Haar cascades for face recognition
        self.matcher = matcher #Helper function to run the model-powered face recognizer
 
        pygame.mixer.init()
        self.alarm_sound = pygame.mixer.Sound(resource_path('Alarm.mp3')) #Sound file for alarm
        self.alarm_sound.set_volume(1.0) #Set its volume
 
        # Identity check throttling
        self.last_identity = None #Blank slate on last known identity
        self.last_recognition_time = 0.0 #Set recognition time to 0
 
        # Departure / return debounce state
        self.absence_start_time = None #Set the value to none
        self.away_confirmed = False #Assume 'enzo' is initially on screen
        self.return_pending_since = None #Set the value to none
 
        # Proximity / alarm state
        self.close_distance_start_time = None #No set time for distance checking
        self.locked = False #Device is as is. Not locked for now
        self.alarm_triggered_since_away = False #Flag for triggering alarm is initially off. 
        self._alarm_was_playing = False #Set the alarm initially to off
        self._pending_warning_speech = False #No warning phrase let out initially
 
        self.cap = None #No set cap
        self.running = False #Currently not running
        self.on_stop_callback = on_stop_callback

    def camera_start(self, show_window=True): #Helper function to run the camera
        self.running = True #Enable running
        self.show_window = show_window #Pop out a window
 
        self.cap = cv2.VideoCapture(0) #Enable capture
        if not self.cap.isOpened():
            print("Cannot Open Camera!")
            return False
 
        print("Camera opened successfully. Press 'q' to quit.")
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        return True
    
    def _detection_loop(self): #Detection loop to start detecting faces
        while self.running: #Conditions to run while the camera is running
            ret, frame = self.cap.read()
            if not ret:
                print("Can't retrieve frame (stream end?). Exiting....")
                break
 
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = self.face_cascade.detectMultiScale(
                rgb_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
 
            if len(faces) > 0: #If the number of faces is more than 0
                # Largest detected face = the one closest to camera
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                face_area = w * h
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                self._handle_face_present(rgb_frame, face_area)
           
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                identity = self.last_identity if self.last_identity else "..."
                label = f"{identity} ({face_area})"
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                self._handle_face_absent()
 
            self._check_pending_warning_speech()
 
            if self.show_window:
                cv2.imshow('Intruder Alert', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop()
                    break
            else:
                time.sleep(0.03)
 
        self.cap.release()
        cv2.destroyAllWindows()

    # ── Identity + proximity handling ──
    def _handle_face_present(self, rgb_frame, face_area):
        now = time.time() #Acquire the current time
 
        if now - self.last_recognition_time >= RECOGNITION_INTERVAL_SECONDS:
            pil_image = Image.fromarray(rgb_frame) 
            identity, _ = self.matcher.identity(pil_image)
            self.last_identity = identity
            self.last_recognition_time = now
 
        if self.last_identity == "enzo":
            self.close_distance_start_time = None
            self._handle_enzo_present()
        elif self.last_identity in ("rafiq", "unknown"):
            self._handle_intruder_present(face_area)
    
    def _handle_enzo_present(self): #Helper function to handle if whether or not Enzo is within the frame or not.
        if self.away_confirmed:
            # Enzo's face has reappeared after a confirmed absence
            if self.return_pending_since is None:
                self.return_pending_since = time.time()
            elif time.time() - self.return_pending_since >= RETURN_CONFIRM_SECONDS:
                self._on_enzo_return()
        else:
            self.absence_start_time = None
            self.return_pending_since = None


    def _handle_intruder_present(self, face_area): #Helper function to handle whenever Rafiq (the intruder) gets into the frame
        now = time.time()
 
        if face_area >= PROXIMITY_AREA_THRESHOLD:
            if self.close_distance_start_time is None:
                self.close_distance_start_time = now
            elif (now - self.close_distance_start_time >= PROXIMITY_HOLD_SECONDS
                  and not self.locked):
                self._trigger_alarm_and_lock()
        else:
            self.close_distance_start_time = None

    def _handle_face_absent(self): #Helper function to handle absence within the frame
        self.close_distance_start_time = None
 
        if not self.away_confirmed:
            now = time.time()
            if self.absence_start_time is None:
                self.absence_start_time = now
            elif now - self.absence_start_time >= AWAY_CONFIRM_SECONDS:
                self.away_confirmed = True

        # ── Alarm / lock / return actions ──
    def _trigger_alarm_and_lock(self):
        self.locked = True
        self.alarm_triggered_since_away = True
        self.alarm_sound.play()
        self._pending_warning_speech = True  # spoken once the alarm sound finishes
 
        _minimize_all_windows()
        _lock_workstation()

    def _check_pending_warning_speech(self):
        # Same audio-sequencing pattern as Sleep Alarm: never speak over the alarm sound.
        alarm_busy = pygame.mixer.get_busy()
 
        if alarm_busy:
            self._alarm_was_playing = True
        elif self._alarm_was_playing:
            self._alarm_was_playing = False
            if self._pending_warning_speech:
                self._pending_warning_speech = False
                speak(get_red_handed_ack())
 
    def _on_enzo_return(self):
        speak("Welcome back, Master!")
        if self.alarm_triggered_since_away:
            speak("While you were away, Rafiq tried to sneak up and tamper with your device. Luckily, I was able to stop him. No need to thank me, Master.")
        else:
            speak("Now, back to business as usual.")
 
        self.away_confirmed = False
        self.alarm_triggered_since_away = False
        self.absence_start_time = None
        self.return_pending_since = None
        self.locked = False
 
    def stop(self):
        self.running=False
        pygame.mixer.stop()
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

        if hasattr(self, "detector") and self.detector:
            self.detector.close()

        #Call the callback when stopping
        if self.on_stop_callback:
            self.on_stop_callback()
        cv2.destroyAllWindows()
