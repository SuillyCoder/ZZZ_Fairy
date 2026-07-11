#Importing dependencies
import os, subprocess
from pynput import keyboard #Import keyboard input
from .bridge import fairy_bridge #Import the bridging code

#Execution functions
def on_mute_hotkey():
    muted = fairy_bridge.toggle_mute() #Toggle mute
    print(f"[Hotkey] Fairy is now {'muted' if muted else 'unmuted'}.")

def clear_terminal():
    subprocess.run('cls', shell=True)

def hide_icon():
    fairy_bridge.toggle_visibility_requested.emit() #Ask the GUI thread to flip window visibility

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