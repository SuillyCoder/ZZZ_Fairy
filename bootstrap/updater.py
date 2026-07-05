# bootstrap/updater.py
import subprocess, sys, os

def _get_repo_dir():
    if getattr(sys, "frozen", False):
        # Frozen exe: point at your real git checkout, not the bundled copy
        return r"C:\Users\enzoa\OneDrive\Documents\GitHub\ZZZ_Fairy"
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPO_DIR = _get_repo_dir()
REMOTE_URL = "https://github.com/SuillyCoder/ZZZ_Fairy.git"

def _run(args):
    try:
        return subprocess.run(args, cwd=REPO_DIR, capture_output=True, text=True, timeout=15)
    except FileNotFoundError as e:
        print(f"[Updater] git executable not found on PATH: {e}")
        return None
    except subprocess.TimeoutExpired as e:
        print(f"[Updater] git command timed out: {e}")
        return None
    except OSError as e:
        print(f"[Updater] OS error running git: {e}")
        return None

def check_and_update() -> bool:
    """Returns True if an update was applied (caller should restart)."""
    local_result = _run(["git", "rev-parse", "HEAD"])
    if local_result is None:
        return False  # git unavailable or repo missing — fail open, don't block boot
    local = local_result.stdout.strip()

    remote_result = _run(["git", "ls-remote", REMOTE_URL, "HEAD"])
    if remote_result is None:
        return False
    remote_out = remote_result.stdout.strip()
    remote = remote_out.split()[0] if remote_out else None

    if not remote or remote == local:
        return False

    print("[Updater] New version detected on GitHub, syncing local checkout...")
    _run(["git", "stash", "--include-untracked"])
    pull = _run(["git", "pull", "--ff-only", "origin", "main"])
    if pull is None or pull.returncode != 0:
        print("[Updater] Pull failed, staying on current version.")
        return False
    
    if getattr(sys, "frozen", False):
        print("[Updater] Repo checkout updated, Master — but this running .exe "
              "is still the old build. Rebuild with PyInstaller to apply the changes.")
    else:
        print("[Updater] Updated to latest commit.")
    return True

def force_sync() -> bool: #Just in case first time automated sync does not work. 
    fetch = _run(["git", "fetch", "origin", "main"])
    if fetch is None or fetch.returncode != 0:
        print("[Updater] force_sync: fetch failed.")
        return False
    reset = _run(["git", "reset", "--hard", "origin/main"])
    if reset is None or reset.returncode != 0:
        print("[Updater] force_sync: reset failed.")
        return False
    print("[Updater] force_sync: repo hard-reset to origin/main.")
    return True

def restart():
    os.execv(sys.executable, [sys.executable] + sys.argv)