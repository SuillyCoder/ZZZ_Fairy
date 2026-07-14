#Importing dependencies
import os, subprocess
from pynput import keyboard #Import keyboard input
from .bridge import fairy_bridge #Import the bridging code

#Module-level files
_stop_event = None
_transcription_listener = None

#Execution functions
def on_mute_hotkey():
    muted = fairy_bridge.toggle_mute() #Toggle mute
    print(f"[Hotkey] Fairy is now {'muted' if muted else 'unmuted'}.")

def clear_terminal():
    subprocess.run('cls', shell=True)

def hide_icon():
    fairy_bridge.toggle_visibility_requested.emit() #Ask the GUI thread to flip window visibility

def set_transcription_stop_event(stop_event):
    global _stop_event
    _stop_event = stop_event

def end_transcription():
    print("Transcription ended. Please wait for full transcript")
    if _stop_event is not None: #If the transcribing process hasn't stopped yet...
        _stop_event.set() #Stop it entirely


#Listener threads
def start_mute_hotkey_listener(): #Asynchronous thread to listen for being muted 
    listener = keyboard.GlobalHotKeys({"<ctrl>+<alt>+m": on_mute_hotkey}) #Listen for the Ctrl + Shift + M combo
    listener.daemon = True #Enable the daemon thread
    listener.start() #Start listening for key presses
    return listener

def start_clear_hotkey_listener():
    listener = keyboard.GlobalHotKeys({"<ctrl>+<alt>+c": clear_terminal}) #Listen for the Ctrl + Shift + M combo
    listener.daemon = True #Enable the daemon thread
    listener.start() #Start listening for key presses
    return listener

def start_hide_icon_listener():
    listener = keyboard.GlobalHotKeys({"<ctrl>+<alt>+h": hide_icon}) #Listen for the Ctrl + Shift + M combo
    listener.daemon = True #Enable the daemon thread
    listener.start() #Start listening for key presses
    return listener

def start_end_transcription_listener():
    listener = keyboard.GlobalHotKeys({"<ctrl>+<alt>+t": end_transcription}) #Listen for the Ctrl + Shift + M combo
    listener.daemon = True #Enable the daemon thread
    listener.start() #Start listening for key presses
    return listener

def stop_end_transcription_listener():
    global _transcription_listener, _stop_event
    if _transcription_listener is not None: #If the thread is continuously listening...
        _transcription_listener.stop() #Stop it
        _transcription_listener = None #Set it to none
    _stop_event = None


