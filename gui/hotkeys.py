from pynput import keyboard #Import keyboard input
from .bridge import fairy_bridge #Import the bridging code

def on_mute_hotkey():
    muted = fairy_bridge.toggle_mute() #Toggle mute
    print(f"[Hotkey] Fairy is now {'muted' if muted else 'unmuted'}.")

def start_mute_hotkey_listener(): #Asynchronous thread to listen for being muted 
    listener = keyboard.GlobalHotKeys({"<ctrl>+<alt>+m": on_mute_hotkey}) #Listen for the Ctrl + Shift + M combo
    listener.daemon = True #Enable the daemon thread
    listener.start() #Start listening for key presses
    return listener