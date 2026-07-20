import sys, os, subprocess, glob
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import PROTONVPN_EXE_PATH, FIREFOX_PATH

def find_protonvpn_exe():
    if PROTONVPN_EXE_PATH and os.path.isfile(PROTONVPN_EXE_PATH): #Check for the filepath for ProtonVPN
        return PROTONVPN_EXE_PATH
    matches = glob.glob(r"C:\Program Files\Proton\VPN*\ProtonVPN.exe") #Use glob to extract Unix-based filepath format in order to find it
    return matches[0] if matches else None #Return a match if it finds it.

def open_protonvpn_app(): 
    exe_path = find_protonvpn_exe #Extract the ProtonVPN file
    if not exe_path:
        raise RuntimeError("Couldn't locate ProtonVPN.exe — set PROTONVPN_EXE_PATH in your .env to the exact path.")
    subprocess.Popen([exe_path]) #Run a subprocess to open the exe path

def open_browser_to(url: str):
    subprocess.Popen([FIREFOX_PATH, url]) #Open the site url in Firefox via the Popen subproces
