#Main handler file

import threading

from computer_vision import cv_state
from computer_vision.intruder_alert.face_matcher import FaceMatcher
from computer_vision.intruder_alert.intruder_camera import IntruderAlertCamera

matcher = None
active_camera = None
_lock = threading.Lock()


def _on_camera_stopped():
    global active_camera
    with _lock:
        active_camera = None
    cv_state.deactivate("guard")


def handle_intruder_alert(voice_query: str = "") -> str:
    global matcher, active_camera

    if matcher is None:
        try:
            matcher = FaceMatcher()
        except FileNotFoundError as e:
            return f"I can't start Intruder Alert yet, Master — {e}"

    with _lock:
        if active_camera is not None:
            return "I'm already keeping watch, Master."

        camera = IntruderAlertCamera(matcher, on_stop_callback=_on_camera_stopped)
        cv_state.activate("guard", camera.stop)   # force-stops Sleep Alarm if it's running
        started = camera.camera_start(show_window=True)

        if not started:
            cv_state.deactivate("guard")
            return "I couldn't access the camera, Master. Please check it's not already in use."

        active_camera = camera

    return "Keeping watch now, Master. I'll let you know if anything happens."