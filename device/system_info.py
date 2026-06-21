import os, sys, subprocess, tempfile, shutil, psutil, threading

#Import via the absolute file path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#Byte size reader
def bytes_to_readable(num_bytes: int) -> str: #Convert byte digit to string
    step = 1024.0
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < step: #If the number of bytes is lesser than the step value
            return f"{num_bytes: .2f} {unit}" #Return the current reading
        num_bytes /= step #Divide the num bytes by the step for conversion

        return f"{num_bytes: .2f} PB"

def get_battery_info():
    #Assign some battery info to a variable
    battery = psutil.sensors_battery() #psutil helper function to return battery info from sensors
    
    if battery is None: #NO battery info detected, return nothing
        return None, None 
    return battery.percent, battery.power_plugged #Otherwise, return current percentages and power plugged in

# ============== CORE MONITORING ===============#

# System Performance
def get_system_performance() -> str: 
    #Variables to obtain CPU, RAM, and SSD Metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.splitdrive(sys.executable)[0] + "\\" if os.name == "nt" else "/")

    device_feedback = [ #Hardcoded lines to provide feedback on device performance
        f"CPU usage is at {cpu_percent:.0f} percent.",
        f"RAM usage is at {ram.percent:.0f} percent, with {bytes_to_readable(ram.used)} used out of {bytes_to_readable(ram.total)}.",
        f"Disk usage is at {disk.percent:.0f} percent.",
    ]

    battery_percent, plugged_in = get_battery_info() #Obtain information from battery helper function'
    if battery_percent is not None: #As long as the battery is not low-bat
        plug_status = "and currently charging" if plugged_in else "and currently not charging" #Tells if the device is charging or not
        device_feedback.append(f"Battery is at {battery_percent:.0f} percent, {plug_status}.")
    else:
        device_feedback.append("No battery detected — this looks like a desktop system.") #No battery detected
 
    return " ".join(device_feedback) #String the feedback together

#Battery thresholds
_tiers_fired = set()  # Tracks which tiers already warned this discharge cycle

def check_battery_threshold() -> str | None:
    battery_percent, plugged_in = get_battery_info()
    if battery_percent is None:
        return None  # No battery to worry about (desktop)

    if plugged_in or battery_percent > 30:
        _tiers_fired.clear()  # Recovered — allow tiers to fire again next discharge
        return None

    for tier in (30, 20, 10, 5):  # check highest-to-lowest so the most urgent message wins
        if battery_percent <= tier and tier not in _tiers_fired:
            _tiers_fired.add(tier)
            if tier == 30:
                return f"Master, you are at {battery_percent:.0f} percent. Switching to low power operation mode. I suggest you charge your device if you still want me around."
            elif tier == 20:
                return f"Master, you are at {battery_percent:.0f} percent. System performance may decline. I think you should really charge your device now, master."
            elif tier == 10:
                return f"Master, you are at {battery_percent:.0f} percent. Approaching critically low power level. Now might be a really good idea to charge your device, master."
            elif tier == 5:
                return f"Master, you are at {battery_percent:.0f} percent. Shutdown imminent. I guess this is where I flatline, Master. I told you you should have charged your device."
    return None


def start_battery_monitor(speak_fn, poll_interval=60):
    """Runs check_battery_threshold() in a background daemon thread, calling speak_fn() on a hit."""
    def _loop():
        while True:
            warning = check_battery_threshold()
            if warning:
                speak_fn(warning)
            threading.Event().wait(poll_interval)
    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread

# Cache and Temp File Clearing (Preview)
def preview_cache_clear() -> tuple[str, str]:
    temp_dir = tempfile.gettempdir() #Acquire temporary directory
    total_size = 0
    file_count = 0

    for root, dirs, files, in os.walk(temp_dir):
        for f in files:
            try: 
                #Acquire the file path and directory
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
                file_count += 1
            except(OSError, PermissionError):
                continue #Skip the files we can't stat

    if file_count == 0:
        return "Your temp cache is already clean, Master. Nothing to clear.", temp_dir
 
    summary = (
        f"I found {file_count} temporary files taking up {bytes_to_readable(total_size)} "
        f"in your temp cache. Shall I clear them, Master?"
    )
    return summary, temp_dir
 
 # Cache and Temp File Clearing (Actual Cleaning)
def clear_cache(temp_dir: str) -> str:
    cleared = skipped = freed_bytes = 0 #Variables for indicating cleaned status

    for entry in os.listdir(temp_dir):
        full_path = os.path = os.path.join(temp_dir, entry) #Extracting full path for cache file to be cleared
        try: 
            if os.path.isfile(full_path) or os.path.isLink(full_path):
                freed_bytes += os.path.getsize(full_path) #Accumulate freed bytes
                os.remove(full_path)
                cleared += 1
            elif os.path.isdir(full_path):
                # Sum size before removal for an accurate freed-space report
                dir_size = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, _, files in os.walk(full_path)
                    for f in files
                    if os.path.exists(os.path.join(dp, f))
                )
                shutil.rmtree(full_path, ignore_errors=True)
                freed_bytes += dir_size
                cleared += 1
        except(PermissionError, OSError): #Exception for permission error or OS error
            skipped+= 1
            continue

    result = f"Cleared {cleared} items, freeing up {bytes_to_readable(freed_bytes)}."
    if skipped:
        result += f" {skipped} items were in use and couldn't be removed."
    return result

#=== Desktop Operations ====#

def open_task_manager_performance() -> str:
    try:
        subprocess.Popen(["taskmgr", "/7"]) #Open up task manager for performance
        return "Opening Task Manager's performance tab for you, Master."
    except FileNotFoundError: #If Fairy fails to detect task manager (kinda impossible though, no??)
        return "I couldn't find Task Manager on this system, Master."
    except Exception: #Unexpected error thrown
        return "Something went wrong trying to open Task Manager, Master."
