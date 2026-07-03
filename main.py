# main.py — thin shim, keeps old terminal-only entry point working
from main_wrapped import run
if __name__ == "__main__":
    run()