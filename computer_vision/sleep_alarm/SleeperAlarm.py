import threading 
from computer_vision.sleep_alarm.SleeperBeeperCam import SleeperBeeperCamera

active_camera = None
lock = threading.Lock()

def on_camera_stopped():
    global active_camera #Set the active camera variable as a global one
    with lock:
        active_camera = None #If the thread is locked, disable the camera

def handle_sleep_alarm(voice_query: str = "") -> str: 
    global active_camera
    with lock: 
        if active_camera is not None:
            return "Sleep Alarm is already watching over you, Master."
        camera = SleeperBeeperCamera(on_stop_callback = on_camera_stopped)
        started = camera.camera_start(show_window=True)

        if not started:
            return "I couldn't access the camera, Master. Please check it's not already in use."
 
        active_camera = camera
 
    return "Keeping an eye on you now, Master. I'll let you know if you start dozing off."
 