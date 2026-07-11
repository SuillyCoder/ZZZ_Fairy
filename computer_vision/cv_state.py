#Handles exclusive access of the camera for only a single daemon

import threading
lock = threading.Lock()
active_feature = None #Options are either "sleep" or "guard" for now
active_stop_fn = None # no-argument callable that force-stops the active feature

def activate(feature_name: str, stop_fn): #Attempts to claim the camera for a certain feature
    global active_feature, active_stop_fn
    with lock:
        if active_feature is not None and active_feature != feature_name:
            previous_stop_fn = active_stop_fn
            if previous_stop_fn:
                previous_stop_fn()  # forcefully release the camera now
 
        active_feature = feature_name
        active_stop_fn = stop_fn
    
def deactivate(feature_name: str): #Releases the camera claim held by another process, if there is one
    global active_feature, active_stop_fn
    with lock:
        if active_feature == feature_name:
            active_feature = None
            active_stop_fn = None
    
